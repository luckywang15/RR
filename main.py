import wx
import os
import time
import threading
import logging
from typing import List
# import the newly created GUI file
import cdframe


class PCB:
    def __init__(self):
        self.PName = ''  # 进程名称
        self.PInstructions: List[Instructions] = []  # 进程中的指令列表
        self.CurrentInstruction = 0  # 当前运行指令索引


class Instructions:
    def __init__(self):
        self.IName = ''  # 指令类型
        self.IRunTime = 0  # 指令运行时间
        self.IRemainTime = 0  # 指令剩余运行时间


# 各种队列
AllQue: List[PCB] = []
ReadyQue: List[PCB] = []
BackupReadyQue: List[PCB] = []
InputQue: List[PCB] = []
OutputQue: List[PCB] = []
WaitQue: List[PCB] = []
# 时间片数
timeSlices = 0
# 线程锁
lock = threading.Lock()
# 线程阻塞
ent = threading.Event()
# 通过单双判断是暂停还是继续调度
count = 0
# 打印日志
logging.basicConfig(filename='logger.log', level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class CalcFrame(cdframe.MyFrame1):
    def __init__(self, parent):
        cdframe.MyFrame1.__init__(self, parent)

    def showQue(self, quename, where):
        name = []
        for j in range(len(quename)):
            name.append(quename[j].PName)
        where.SetValue('\n'.join(name))

    # def showlog(self, quename):
    #     name = []
    #     for k in range(len(quename)):
    #         name.append(quename[k].PName)
    #     return name

    def initQue(self):
        global lock
        # 打开互斥锁
        lock.acquire()
        BackupReadyQue[:] = AllQue[:]
        for p in AllQue:
            self.m_textCtrl2.SetValue('初始化......')
            time.sleep(0.3)
            ReadyQue.append(p)
            BackupReadyQue.remove(p)
            self.showQue(ReadyQue, self.m_textCtrl3)
            self.showQue(BackupReadyQue, self.m_textCtrl4)
        # 根据首指令分配等待队列
        for pcb in AllQue:
            self.m_textCtrl2.SetValue('分配队列中...')
            if len(pcb.PInstructions) > 0:
                # 排除Pi H00这种空指令进程
                if pcb.PInstructions[0].IName == 'C':
                    ReadyQue.append(ReadyQue[0])
                    self.showQue(ReadyQue, self.m_textCtrl3)
                elif pcb.PInstructions[0].IName == 'I':
                    InputQue.append(ReadyQue[0])
                    self.showQue(InputQue, self.m_textCtrl5)
                elif pcb.PInstructions[0].IName == 'O':
                    OutputQue.append(ReadyQue[0])
                    self.showQue(OutputQue, self.m_textCtrl6)
                elif pcb.PInstructions[0].IName == 'W':
                    WaitQue.append(ReadyQue[0])
                    self.showQue(WaitQue, self.m_textCtrl7)
                # elif pcb.PInstructions[0].IName == 'H':
                else:
                    ReadyQue.pop(0)
                    self.showQue(ReadyQue, self.m_textCtrl3)
                    continue
                ReadyQue.pop(0)
                self.showQue(ReadyQue, self.m_textCtrl3)
                time.sleep(0.3)
            else:
                ReadyQue.pop(0)
                self.showQue(ReadyQue, self.m_textCtrl3)
                time.sleep(0.3)
        # 释放互斥锁
        lock.release()

    def startque(self):
        logger.info('---------正在进行调度---------')
        global ent
        self.initQue()
        ent.set()
        while len(ReadyQue) > 0 or len(InputQue) > 0 or len(OutputQue) > 0 or len(WaitQue) > 0:
            ent.wait()
            logger.info('就绪队列：' + ' '.join([que.PName for que in ReadyQue]))
            logger.info('输入等待队列：' + ' '.join([que.PName for que in InputQue]))
            logger.info('输出等待队列：' + ' '.join([que.PName for que in OutputQue]))
            logger.info('其它等待队列：' + ' '.join([que.PName for que in WaitQue]))
            self.runReady()
            self.runIn()
            self.runOut()
            self.runWait()
            logger.info('--------------------------')
        self.m_textCtrl2.SetValue('')
        logger.info('---------调度完成---------')

    def runReady(self):
        # 就绪队列执行
        global timeSlices
        # 获取时间片大小
        tim = int(self.m_textCtrl1.GetValue())
        if len(ReadyQue) > 0:
            # 时间片大于或等于当前指令所需时间，进程提前释放CPU
            if ReadyQue[0].PInstructions[0].IRemainTime <= tim:
                timeSlices = ReadyQue[0].PInstructions[0].IRemainTime
                ReadyQue[0].PInstructions.pop(0)
                if len(ReadyQue[0].PInstructions) > 0:
                    # 根据下条指令分配队列
                    if ReadyQue[0].PInstructions[0].IName == 'C':
                        ReadyQue.append(ReadyQue[0])
                        self.showQue(ReadyQue, self.m_textCtrl3)
                    elif ReadyQue[0].PInstructions[0].IName == 'I':
                        InputQue.append(ReadyQue[0])
                        self.showQue(InputQue, self.m_textCtrl5)
                    elif ReadyQue[0].PInstructions[0].IName == 'O':
                        OutputQue.append(ReadyQue[0])
                        self.showQue(OutputQue, self.m_textCtrl6)
                    elif ReadyQue[0].PInstructions[0].IName == 'W':
                        WaitQue.append(ReadyQue[0])
                        self.showQue(WaitQue, self.m_textCtrl7)
                    else:
                        pass
                    ReadyQue.remove(ReadyQue[0])
                    self.showQue(ReadyQue, self.m_textCtrl3)
                else:
                    ReadyQue.remove(ReadyQue[0])
                    self.showQue(ReadyQue, self.m_textCtrl3)
            else:
                timeSlices = tim
                ReadyQue[0].PInstructions[0].IRunTime += tim
                ReadyQue[0].PInstructions[0].IRemainTime -= tim
                ReadyQue.append(ReadyQue[0])
                self.showQue(ReadyQue, self.m_textCtrl3)
                ReadyQue.pop(0)
                self.showQue(ReadyQue, self.m_textCtrl3)
            # 显示当前运行进程
            if len(ReadyQue) > 0:
                self.m_textCtrl2.SetValue(ReadyQue[0].PName)
                time.sleep(0.3)

    def runIn(self):
        # 输入等待队列执行
        global timeSlices
        tem = timeSlices
        if len(InputQue) > 0:
            while tem != 0 and len(InputQue) > 0:
                if InputQue[0].PInstructions[0].IRemainTime <= tem:
                    tem -= InputQue[0].PInstructions[0].IRemainTime
                    InputQue[0].PInstructions.pop(0)
                    if len(InputQue[0].PInstructions) > 0:
                        if InputQue[0].PInstructions[0].IName == 'C':
                            ReadyQue.append(InputQue[0])
                            self.showQue(ReadyQue, self.m_textCtrl3)
                            if len(ReadyQue) == 1:
                                # 提前更新当前运行进程窗口
                                self.m_textCtrl2.SetValue(ReadyQue[0].PName)
                        elif InputQue[0].PInstructions[0].IName == 'I':
                            InputQue.append(InputQue[0])
                            self.showQue(InputQue, self.m_textCtrl5)
                        elif InputQue[0].PInstructions[0].IName == 'O':
                            OutputQue.append(InputQue[0])
                            self.showQue(OutputQue, self.m_textCtrl6)
                        elif InputQue[0].PInstructions[0].IName == 'W':
                            WaitQue.append(InputQue[0])
                            self.showQue(WaitQue, self.m_textCtrl7)
                        # elif InputQue[0].PInstructions[0].IName == 'H':
                        else:
                            pass
                        InputQue.remove(InputQue[0])
                        self.showQue(InputQue, self.m_textCtrl5)
                        time.sleep(0.3)
                    else:
                        InputQue.remove(InputQue[0])
                        self.showQue(InputQue, self.m_textCtrl5)
                        time.sleep(0.3)
                else:
                    InputQue[0].PInstructions[0].IRunTime += tem
                    InputQue[0].PInstructions[0].IRemainTime -= tem
                    tem = 0

    def runOut(self):
        # 执行输出等待队列
        global timeSlices
        tem = timeSlices
        if len(OutputQue) > 0:
            while tem != 0 and len(OutputQue) > 0:
                if OutputQue[0].PInstructions[0].IRemainTime <= tem:
                    tem -= OutputQue[0].PInstructions[0].IRemainTime
                    OutputQue[0].PInstructions.pop(0)
                    if len(OutputQue[0].PInstructions) > 0:
                        if OutputQue[0].PInstructions[0].IName == 'C':
                            ReadyQue.append(OutputQue[0])
                            self.showQue(ReadyQue, self.m_textCtrl3)
                            if len(ReadyQue) == 1:
                                self.m_textCtrl2.SetValue(ReadyQue[0].PName)
                        elif OutputQue[0].PInstructions[0].IName == 'I':
                            InputQue.append(OutputQue[0])
                            self.showQue(InputQue, self.m_textCtrl5)
                        elif OutputQue[0].PInstructions[0].IName == 'O':
                            OutputQue.append(OutputQue[0])
                            self.showQue(OutputQue, self.m_textCtrl6)
                        elif OutputQue[0].PInstructions[0].IName == 'W':
                            WaitQue.append(OutputQue[0])
                            self.showQue(WaitQue, self.m_textCtrl7)
                        # elif OutputQue[0].PInstructions[0].IName == 'H':
                        else:
                            pass
                        OutputQue.remove(OutputQue[0])
                        self.showQue(OutputQue, self.m_textCtrl6)
                        time.sleep(0.3)
                    else:
                        OutputQue.remove(OutputQue[0])
                        self.showQue(OutputQue, self.m_textCtrl6)
                        time.sleep(0.3)
                else:
                    OutputQue[0].PInstructions[0].IRunTime += tem
                    OutputQue[0].PInstructions[0].IRemainTime -= tem
                    tem = 0

    def runWait(self):
        # 执行其它等待队列
        global timeSlices
        tem = timeSlices
        if len(WaitQue) > 0:
            while tem != 0 and len(WaitQue) > 0:
                if WaitQue[0].PInstructions[0].IRemainTime <= tem:
                    tem -= WaitQue[0].PInstructions[0].IRemainTime
                    WaitQue[0].PInstructions.pop(0)
                    if len(WaitQue[0].PInstructions) > 0:
                        if WaitQue[0].PInstructions[0].IName == 'C':
                            ReadyQue.append(WaitQue[0])
                            self.showQue(ReadyQue, self.m_textCtrl3)
                            if len(ReadyQue) == 1:
                                self.m_textCtrl2.SetValue(ReadyQue[0].PName)
                        elif WaitQue[0].PInstructions[0].IName == 'I':
                            InputQue.append(WaitQue[0])
                            self.showQue(InputQue, self.m_textCtrl5)
                        elif WaitQue[0].PInstructions[0].IName == 'O':
                            OutputQue.append(WaitQue[0])
                            self.showQue(OutputQue, self.m_textCtrl6)
                        elif WaitQue[0].PInstructions[0].IName == 'W':
                            WaitQue.append(WaitQue[0])
                            self.showQue(WaitQue, self.m_textCtrl7)
                        # elif WaitQue[0].PInstructions[0].IName == 'H':
                        else:
                            pass
                        WaitQue.remove(WaitQue[0])
                        self.showQue(WaitQue, self.m_textCtrl7)
                        time.sleep(0.3)
                    else:
                        WaitQue.remove(WaitQue[0])
                        self.showQue(WaitQue, self.m_textCtrl7)
                        time.sleep(0.3)
                else:
                    WaitQue[0].PInstructions[0].IRunTime += tem
                    WaitQue[0].PInstructions[0].IRemainTime -= tem
                    tem = 0

    def openfile(self, event):
        # 清空队列
        AllQue.clear()
        ReadyQue.clear()
        BackupReadyQue.clear()
        InputQue.clear()
        OutputQue.clear()
        WaitQue.clear()
        self.m_textCtrl2.SetValue('')
        self.m_textCtrl3.SetValue('')
        self.m_textCtrl4.SetValue('')
        self.m_textCtrl5.SetValue('')
        self.m_textCtrl6.SetValue('')
        self.m_textCtrl7.SetValue('')
        wildcard = "Text Files (*.txt)|*.txt"
        dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            with open(dlg.GetPath(), 'r') as fp:
                currentPCB: PCB
                for line_text in fp:
                    if line_text[0] == 'P':
                        currentPCB = PCB()
                        currentPCB.PName = line_text.strip()
                        # print(currentPCB.PName)
                    elif line_text[0] == 'C' or line_text[0] == 'I' or line_text[0] == 'O' or line_text[0] == 'W':
                        i = Instructions()
                        i.IName = line_text[0]
                        i.IRunTime = 0
                        i.IRemainTime = int(line_text[1:])
                        currentPCB.PInstructions.append(i)
                    elif line_text[0] == 'H':
                        AllQue.append(currentPCB)
                    elif line_text == '':
                        fp.close()

    def start(self, event):
        thread = threading.Thread(target=self.startque, )  # 定义线程
        thread.start()

    def suspend(self, event):
        global ent, count
        count += 1
        if count % 2 == 0:
            logger.info('---------恢复调度---------')
            ent.set()
        else:
            logger.info('---------暂停调度---------')
            ent.clear()


def main():
    app = wx.App(False)
    frame = CalcFrame(None)
    frame.Show(True)
    # start the applications
    app.MainLoop()


if __name__ == '__main__':
    main()
