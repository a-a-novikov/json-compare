from typing import Any


class LogProcessor:
    def __init__(self) -> None:
        self.log: list[str] = list()
        self.curr_path: str = str()
        self.missing_prop: list[str, int] = ["missing_obj_property", 0]
        self.incor_type: list[str, int] = ["incorrect_type", 0]
        self.lack_of_items: list[str, int] = ["lack_of_array_items", 0]
        self.exceed_items: list[str, int] = ["exceeding_array_items", 0]
        self.unequal_val: list[str, int] = ["unequal_value", 0]
        self.miss_arr_item: list[str, int] = ["missing_array_itme", 0]
        self.diffs_counters = [
            self.missing_prop, self.incor_type, self.lack_of_items,
            self.exceed_items, self.unequal_val, self.miss_arr_item,
        ]

    def setup_path(self, prev_path: str, key: str) -> None:
        if prev_path:
            self.curr_path = prev_path + f".{key}"
        else:
            self.curr_path = f".{key}"

    def missing_property(self) -> None:
        msg = self.curr_path + "\nproperty is missing"
        self.log.append(msg)
        self.missing_prop[1] += 1

    def incorrect_type(
            self,
            exp_obj: int | float | str | bool | dict[str, Any] | list[Any] | None,
            act_obj: int | float | str | bool | dict[str, Any] | list[Any] | None,
    ) -> None:
        exp_obj_type = self.__convert_to_json_type(exp_obj)
        act_obj_type = self.__convert_to_json_type(act_obj)
        msg = (
            self.curr_path + f"\nincorrect type: expected {exp_obj_type}, "
            f"got {act_obj_type} instead"
        )
        self.log.append(msg)
        self.incor_type[1] += 1

    def lack_of_array_items(self, exp_len: int, act_len: int) -> None:
        msg = (
            self.curr_path
            + f"\nlack of items in array: expected {exp_len} items, got only {act_len}"
        )
        self.log.append(msg)
        self.lack_of_items[1] += 1

    def exceeding_array_items(self, exp_len: int, act_len: int) -> None:
        msg = (
            self.curr_path
            + f"\ntoo much items in array: expected {exp_len} items, got {act_len}"
        )
        self.log.append(msg)
        self.exceed_items[1] += 1

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
            + f"\nunequal values: expected {exp_value}, got {act_value} instead"
        )
        self.log.append(msg)
        self.unequal_val[1] += 1

    def missing_array_item(
        self,
        exp_value: int | float | str | bool | dict[str, Any] | list[Any] | None,
        key_prop: str | None = None,
    ) -> None:
        if isinstance(exp_value, str):
            exp_value = f'"{exp_value}"'
        if isinstance(exp_value, dict):
            exp_value = f"<object>"
        if isinstance(exp_value, list):
            exp_value = f"<array>"
        if key_prop:
            exp_value = f'<object> with "{key_prop}"={exp_value}'
        msg = self.curr_path + f"\nmissing array item: expected {exp_value}"
        self.log.append(msg)
        self.miss_arr_item[1] += 1

    def setup_summary(self) -> None:
        summary = (
            f"---------------------"
            f"\nTOTAL: {len(self.log)} differences\n"
        )
        for counter in self.diffs_counters:
            if counter[1]:
                summary += f"-{counter[0]}: " + f"{counter[1]}\n"
        self.log.append(summary)

    @staticmethod
    def __convert_to_json_type(
        item: int | float | str | bool | dict[str, Any] | list[Any] | None,
    ) -> str:
        if isinstance(item, int):
            return "<int>"
        elif isinstance(item, float):
            return "<float>"
        elif isinstance(item, str):
            return "<str>"
        elif isinstance(item, bool):
            return "<bool>"
        elif isinstance(item, dict):
            return "<object>"
        elif isinstance(item, list):
            return "<array>"
        else:
            return "<null>"
