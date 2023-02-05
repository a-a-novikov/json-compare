from collections import Counter
from typing import Any


class LogProcessor:
    def __init__(self) -> None:
        self.log: list[str] = list()
        self.curr_path: str = str()
        self.diffs_counter: Counter[Any] = Counter(
            {
                "missing_obj_property": 0,
                "incorrect_type": 0,
                "arr_with_lack_of_items": 0,
                "exceeding_array_items": 0,
                "unequal_value": 0,
                "missing_array_item": 0,
            }

        )
        
    def get_summary(self) -> str | None:
        """
        :return: if comparison was performed, with summary differences in format:
        ---------------------
        TOTAL: 4 differences
        -missing_obj_property: 3
        -unequal_value: 4
        """
        if hasattr(self, "summary"):
            return self.summary
        return None

    def _setup_path(self, prev_path: str, key: str) -> None:
        if prev_path:
            self.curr_path = prev_path + f"//{key}"
        else:
            self.curr_path = f"//{key}"

    def _missing_property(self) -> None:
        msg = self.curr_path + "\nproperty is missing"
        self.log.append(msg)
        self.diffs_counter["missing_obj_property"] += 1

    def _incorrect_type(
            self,
            exp_obj: int | float | str | bool | dict[str, Any] | list[Any] | None,
            act_obj: int | float | str | bool | dict[str, Any] | list[Any] | None,
    ) -> None:
        exp_obj_type = self.__convert_to_json_type(exp_obj)
        act_obj_type = self.__convert_to_json_type(act_obj)
        msg = (
            self.curr_path + f"\nincorrect type: expected {exp_obj} ({exp_obj_type}), "
            f"got {act_obj} ({act_obj_type}) instead"
        )
        self.log.append(msg)
        self.diffs_counter["incorrect_type"] += 1

    def _lack_of_array_items(self, exp_len: int, act_len: int) -> None:
        msg = (
            self.curr_path
            + f"\nlack of items in array: expected {exp_len} items, got only {act_len}"
        )
        self.log.append(msg)
        self.diffs_counter["arr_with_lack_of_items"] += 1

    def _exceeding_array_items(self, exp_len: int, act_len: int) -> None:
        msg = (
            self.curr_path
            + f"\ntoo much items in array: expected {exp_len} items, got {act_len}"
        )
        self.log.append(msg)
        self.diffs_counter["exceeding_array_items"] += 1

    def _unequal_values(
        self,
        exp_value: int | float | str | bool | None,
        act_value: int | float | str | bool | None,
    ) -> None:
        if type(exp_value) != type(act_value):
            return self._incorrect_type(exp_value, act_value)

        if isinstance(exp_value, str):
            exp_value = f'"{exp_value}"'
            act_value = f'"{act_value}"'
        msg = (
            self.curr_path
            + f"\nunequal values: expected {exp_value}, got {act_value} instead"
        )
        self.log.append(msg)
        self.diffs_counter["unequal_value"] += 1

    def missing_array_item(
        self,
        key_props_with_values: (
                dict[str, int | float | str | bool | dict[str, Any] | list[Any] | None]
        ),
    ) -> None:
        expected_props = list()
        for key, val in key_props_with_values.items():
            if isinstance(val, str):
                val = f'"{val}"'
            expected_props.append(f'{key}: {val}')
        expected_props_str = ', '.join(expected_props)
        msg = self.curr_path + f"\nmissing array item: expected <object> with {expected_props_str}"
        self.log.append(msg)
        self.diffs_counter["missing_array_item"] += 1

    def _setup_summary(self) -> None:
        summary = (
            f"---------------------"
            f"\nTOTAL: {len(self.log)} differences\n"
        )
        for c_name, c_val in self.diffs_counter.items():
            if c_val:
                summary += f"-{c_name}: " + f"{c_val}\n"
        self.summary: str = summary
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
