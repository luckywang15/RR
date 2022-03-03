import random
from typing import Callable, Dict, Union


def resolve_p_dict(data: Dict[str, Union[int, Callable[[], int]]]):
    return {**data, **{k: v() for k, v in data.items() if callable(v)}}


def random_instructions_iter(
    num: int,
    p_instructions: Dict[str, Union[int, Callable[[], int]]],
    p_needtime: Dict[str, Union[int, Callable[[], int]]],
):
    for _ in range(num):
        sample_p_instructions = resolve_p_dict(p_instructions)
        sum_p_instructions = sum(sample_p_instructions.values())
        random_w_instruction_counter = random.randint(0, sum_p_instructions)
        w_instruction_counter = 0

        for instruction, w_instruction in sample_p_instructions.items():
            w_instruction_counter += w_instruction
            if w_instruction_counter >= random_w_instruction_counter:
                sample_p_needtime = resolve_p_dict(p_needtime)
                yield f"{instruction}{sample_p_needtime[instruction]}"
                break


def main(args):
    pass


if __name__ == "__main__":
    # main(args)
    p_num = 10
    for i in range(p_num):
        print(f"P{i}")
        print(
            "\n".join(
                list(
                    random_instructions_iter(
                        random.randint(10, 100),
                        {"C": 1, "I": 1, "O": 1, "W": 1},
                        {
                            "C": lambda: random.randint(10, 60),
                            "I": lambda: random.randint(10, 60),
                            "O": lambda: random.randint(10, 60),
                            "W": lambda: random.randint(20, 60),
                        },
                    )
                )
            )
        )
        print(f"H")
