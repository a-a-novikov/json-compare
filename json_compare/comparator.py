import datetime
import json
import re
from typing import Any

from .log_processor import LogProcessor


class JSONComparator:
    def __init__(
        self,
        left_file_path: str,
        right_file_path: str,
        target_key_path: str | None = None,
    ):
        self.diff_log: LogProcessor = LogProcessor()
        if target_key_path is not None:
            self.target_key_path: str = target_key_path
        with open(left_file_path, "r") as file:
            self.left_data = json.load(file)
        with open(right_file_path, "r") as file:
            self.right_data = json.load(file)

    def compare_with_right(self) -> None:
        self.diff_log.log.clear()
        self.__edit_t_key_path_root("DATA", "RIGHT")
        self.__compare()
        self.__edit_t_key_path_root("RIGHT", "DATA")

    def compare_with_left(self) -> None:
        self.diff_log.log.clear()
        self.__edit_t_key_path_root("DATA", "LEFT")
        self.__compare(with_actual=False)
        self.__edit_t_key_path_root("LEFT", "DATA")

    def full_compare(self) -> None:
        self.diff_log.log.clear()
        self.__edit_t_key_path_root("DATA", "RIGHT")
        self.__compare()
        self.__edit_t_key_path_root("RIGHT", "LEFT")
        self.__compare(with_actual=False)
        self.__edit_t_key_path_root("LEFT", "DATA")

    def save_diff_logs(self, path: str = "") -> None:
        log_file_name = f"json_compare_diff_{datetime.date.today()}"
        with open(f"{path}{log_file_name}", "w") as f:
            f.write("\n".join(self.diff_log.log))

    def __edit_t_key_path_root(self, from_: str, to: str) -> None:
        if hasattr(self, "target_key_path"):
            self.target_key_path = self.target_key_path.replace(from_, to)

    def __compare(self, with_actual: bool = True) -> None:
        data1, data2, root_log = self.left_data, self.right_data, "RIGHT"
        if not with_actual:
            data1, data2, root_log = data2, data1, "LEFT"

        match self.left_data:
            case dict():
                self._compare_dicts(root_log, data1, data2)
            case list():
                self._compare_lists(root_log, data1, data2)
            case _:
                raise

    def _compare_dicts(
        self, item_path: str, exp_data: dict[str, Any], act_data: dict[str, Any]
    ) -> None:
        for key, val in exp_data.items():
            self.diff_log.setup_path(item_path, key)
            if key not in act_data:
                self.diff_log.missing_key()
                continue
            if type(val) is dict:
                if isinstance(act_data[key], dict):
                    self._compare_dicts(self.diff_log.curr_path, val, act_data[key])
                else:
                    self.diff_log.incorrect_type(dict(), act_data[key])
                continue
            if type(val) is list:
                if isinstance(act_data[key], list):
                    self._compare_lists(self.diff_log.curr_path, val, act_data[key])
                else:
                    self.diff_log.incorrect_type(list(), act_data[key])

                continue
            if val != act_data[key]:
                self.diff_log.unequal_values(val, act_data[key])

    def _compare_lists(
        self, item_path: str, exp_data: list[Any], act_data: list[Any]
    ) -> None:
        if hasattr(self, "target_key_path"):
            self.__compare_with_nested_obj_key_respect(item_path, exp_data, act_data)
        else:
            self.__compare_with_items_order_respect(item_path, exp_data, act_data)

    def __compare_with_items_order_respect(
        self, item_path: str, exp_data: list[Any], act_data: list[Any]
    ) -> None:
        exp_data_len, act_data_len = len(exp_data), len(act_data)
        self.__check_array_lengths(item_path, exp_data_len, act_data_len)

        for idx, val in enumerate(exp_data):
            self.diff_log.setup_path(item_path, f"<array>[{idx}]")
            if idx == act_data_len:
                self.diff_log.missing_array_item(val)
                continue
            if type(val) is dict:
                if isinstance(act_data[idx], dict):
                    self._compare_dicts(self.diff_log.curr_path, val, act_data[idx])
                else:
                    self.diff_log.incorrect_type(dict(), act_data[idx])
                continue
            if type(val) is list:
                if isinstance(act_data[idx], list):
                    self._compare_lists(self.diff_log.curr_path, val, act_data[idx])
                else:
                    self.diff_log.incorrect_type(list(), act_data[idx])

                continue
            if val != act_data[idx]:
                self.diff_log.unequal_values(val, act_data[idx])

    def __compare_with_nested_obj_key_respect(
        self, item_path: str, exp_data: list[Any], act_data: list[Any]
    ) -> None:
        exp_data_len, act_data_len = len(exp_data), len(act_data)
        self.__check_array_lengths(item_path, exp_data_len, act_data_len)

        for idx, val in enumerate(exp_data):
            self.diff_log.setup_path(item_path, f"<array[{idx}]>")
            if type(val) is dict:
                target_key, target_key_val = self.__get_targets_key_value(val)
                act_data_similar_idx = self.__get_idx_of_similar_row(
                    target_key, target_key_val, act_data
                )
                if act_data_similar_idx is None:
                    self.diff_log.missing_array_item(
                        exp_value=target_key_val, spec_key=target_key
                    )
                    continue
                self._compare_dicts(
                    self.diff_log.curr_path, val, act_data[act_data_similar_idx]
                )
                continue
            if type(val) is list:
                if isinstance(act_data[idx], list):
                    self._compare_lists(self.diff_log.curr_path, val, act_data[idx])
                else:
                    self.diff_log.incorrect_type(list(), act_data[idx])

                continue
            if val != act_data[idx]:
                self.diff_log.unequal_values(val, act_data[idx])

    def __check_array_lengths(self, item_path: str, exp_len: int, act_len: int) -> None:
        self.diff_log.setup_path(item_path, f"<array>")
        if exp_len > act_len:
            self.diff_log.lack_of_array_items(exp_len, act_len)
        elif exp_len < act_len:
            self.diff_log.exceeding_array_items(exp_len, act_len)

    def __get_targets_key_value(
        self, object_: dict[str, Any]
    ) -> tuple[str, int | float | str | bool | dict[str, Any] | list[Any] | None]:
        target_key = self.target_key_path.removeprefix(
            re.sub("\[[^()]*\]", "", self.diff_log.curr_path)
        ).replace(".", "")
        exp_key_val = object_[target_key]
        return target_key, exp_key_val

    @staticmethod
    def __get_idx_of_similar_row(
        key: str,
        key_val: int | float | str | bool | dict[str, Any] | list[Any] | None,
        data: list[dict[str, Any]],
    ) -> int | None:
        for idx, obj in enumerate(data):
            act_val = obj.get(key)
            if act_val == key_val:
                return idx
        return None
