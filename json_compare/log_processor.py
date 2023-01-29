from typing import Any


class LogProcessor:
    def __init__(self) -> None:
        self.log: list[str] = list()
        self.curr_path: str = str()

    def setup_path(self, prev_path: str, key: str) -> None:
        if prev_path:
            self.curr_path = prev_path + f".{key}"
        else:
            self.curr_path = f".{key}"

    def missing_key(self) -> None:
        msg = self.curr_path + "\nkey is missing"
        self.log.append(msg)

    def incorrect_type(self, exp_obj: object, act_obj: object) -> None:
        msg = (
            self.curr_path + f"\nincorrect type: expected {type(exp_obj)}, "
            f"got {type(act_obj)} instead"
        )
        self.log.append(msg)

    def lack_of_array_items(self, exp_len: int, act_len: int) -> None:
        msg = (
            self.curr_path
            + f"\nLack of items in array: expected {exp_len} items, got only {act_len}"
        )
        self.log.append(msg)

    def exceeding_array_items(self, exp_len: int, act_len: int) -> None:
        msg = (
            self.curr_path
            + f"\nToo much items in array: expected {exp_len} items, got {act_len}"
        )
        self.log.append(msg)

    def unequal_values(
        self,
        exp_value: int | float | str | bool | None,
        act_value: int | float | str | bool | None,
    ) -> None:
        if type(exp_value) != type(act_value):
            return self.incorrect_type(exp_value, act_value)

        if isinstance(exp_value, str):
            exp_value = f'"{exp_value}"'
            act_value = f'"{act_value}"'
        msg = (
            self.curr_path
            + f"\nUnequal values: expected {exp_value}, got {act_value} instead"
        )
        self.log.append(msg)

    def missing_array_item(
        self,
        exp_value: int | float | str | bool | dict[str, Any] | list[Any] | None,
        spec_key: str | None = None,
    ) -> None:
        if isinstance(exp_value, str):
            exp_value = f'"{exp_value}"'
        if isinstance(exp_value, dict):
            exp_value = f"<object>"
        if isinstance(exp_value, list):
            exp_value = f"<array>"
        if spec_key:
            exp_value = f'<object> with key "{spec_key}"={exp_value}'
        msg = self.curr_path + f"\nMissing array item: expected {exp_value}"
        self.log.append(msg)
