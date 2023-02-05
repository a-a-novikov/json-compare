import datetime
import json
import re
from typing import Any

from .log_processor import LogProcessor


class JSONComparator:
    """
    Provides comparison of two JSON-files.
    """

    def __init__(
        self,
        left_file_path: str,
        right_file_path: str,
        key: str | None = None,
        ignore: str | list[str] | None = None,
        ignore_types: bool = False,
    ):
        """
        :param left_file_path: path to file in .JSON format;
        :param right_file_path: path to file in .JSON format;
        :param key: key for JSON-object's property's name to be a key in comparison
        of similar objects nested in an array. For example, you have:
        {"cats": [{"id": 4, "name": "Nyan"}, {"id": 2, "name": "Marx"}]}. If you want to set
        cat's "id" as a key, use "DATA.cats.<array>.id". DATA points out to the root
        of your JSON and <array> indicates object with key is nested in an array;
        :param ignore: a str or a list of objects' properties whose mismatch should be
        ignored in the process of comparing. Checkout key's paragraph to see examples
        of correct setting the param's items;
        :param ignore_types: set True if you want JSONComparator to ignore type differences
        between similar values like "1.4" vs 1.4 or "[\"New Age №1\"]" vs ["New Age №1"].
        """
        self.diff_log: LogProcessor = LogProcessor()
        self.key: list[str] = list()
        if isinstance(key, list):
            self.key = key
        elif isinstance(key, str):
            self.key = [key]
        self.__match_keys: list[str] = list()
        self.ignore: list[str] = list()
        if isinstance(ignore, list):
            self.ignore = ignore
        elif isinstance(ignore, str):
            self.ignore = [ignore]
        self.ignore_types: bool = ignore_types
        with open(left_file_path, "r") as file:
            self.left_data = json.load(file)
            self.left_f_name: str = file.name
        with open(right_file_path, "r") as file:
            self.right_data = json.load(file)
            self.right_f_name: str = file.name

    def compare_with_right(self) -> None:
        """
        Looks for how the right JSON-file differs from the left one.
        :return: None;
        """
        self.__clear_temp_data()
        self.__edit_key_path_root("DATA", self.right_f_name)
        self.__compare()
        self.__edit_key_path_root(self.right_f_name, "DATA")
        self.diff_log._setup_summary()

    def compare_with_left(self) -> None:
        """
        Looks for how the left JSON-file differs from the right one.
        :return: None;
        """
        self.__clear_temp_data()
        self.__edit_key_path_root("DATA", self.left_f_name)
        self.__compare(with_right=False)
        self.__edit_key_path_root(self.left_f_name, "DATA")
        self.diff_log._setup_summary()

    def full_compare(self) -> None:
        """
        Looks for differences between files from both perspectives.
        :return: None;
        """
        self.__clear_temp_data()
        self.__edit_key_path_root("DATA", self.right_f_name)
        self.__compare()
        self.__edit_key_path_root(self.right_f_name, self.left_f_name)
        self.__compare(with_right=False)
        self.__edit_key_path_root(self.left_f_name, "DATA")
        self.diff_log._setup_summary()

    def save_diff_logs(self, path: str = "") -> None:
        """
        Saves recorded logs as a text file.
        :param path: a path to directory where the log with differences will be saved.
        By default, current work directory will be used;
        :return: None;
        """
        log_file_name = f"json_compare_diff_{datetime.date.today()}"
        with open(f"{path}{log_file_name}", "w") as f:
            f.write("\n".join(self.diff_log.log))

    def __edit_key_path_root(self, from_: str, to: str) -> None:
        self.key = [key.replace(from_, to) for key in self.key]

    def __compare(self, with_right: bool = True) -> None:
        data1, data2, root_log = self.left_data, self.right_data, self.right_f_name
        if not with_right:
            data1, data2, root_log = data2, data1, self.left_f_name

        if isinstance(self.left_data, list) and isinstance(self.right_data, list):
            self.__compare_lists(root_log, data1, data2)
        elif isinstance(self.left_data, dict) and isinstance(self.right_data, dict):
            self.__compare_dicts(root_log, data1, data2)
        else:
            self.diff_log._incorrect_type(self.left_data, self.right_data)

    def __compare_dicts(
        self, item_path: str, exp_data: dict[str, Any], act_data: dict[str, Any]
    ) -> None:
        for key, val in exp_data.items():
            self.diff_log._setup_path(item_path, key)
            if key not in act_data:
                self.diff_log._missing_property()
                continue
            if type(val) is dict:
                self.__try_find_dict_and_compare(val, act_data[key])
                continue
            if type(val) is list:
                self.__try_find_list_and_compare(val, act_data[key])
                continue
            if val != act_data[key] and not self.__key_to_ignore():
                self.__compare_values(val, act_data[key])

    def __compare_lists(
        self, item_path: str, exp_data: list[Any], act_data: list[Any]
    ) -> None:
        self.diff_log._setup_path(item_path, "<array>")
        self.__setup_match_keys()
        if self.__match_keys:
            self.__compare_lists_by_keys(self.diff_log.curr_path, exp_data, act_data)
        else:
            self.__compare_lists_by_order(self.diff_log.curr_path, exp_data, act_data)

    def __compare_lists_by_order(
        self, item_path: str, exp_data: list[Any], act_data: list[Any]
    ) -> None:
        exp_data_len, act_data_len = len(exp_data), len(act_data)
        self.__check_array_lengths(item_path, exp_data_len, act_data_len)

        for idx, val in enumerate(exp_data):
            self.diff_log._setup_path(item_path, f"[{idx}]")
            if idx >= act_data_len:
                break
            if type(val) is dict:
                self.__try_find_dict_and_compare(val, act_data[idx])
                continue
            if type(val) is list:
                self.__try_find_list_and_compare(val, act_data[idx])
                continue
            if val != act_data[idx]:
                self.__compare_values(val, act_data[idx])

    def __compare_lists_by_keys(
        self, item_path: str, exp_data: list[Any], act_data: list[Any]
    ) -> None:
        exp_data_len, act_data_len = len(exp_data), len(act_data)
        self.__check_array_lengths(item_path, exp_data_len, act_data_len)

        for idx, val in enumerate(exp_data):
            self.diff_log._setup_path(item_path, f"[{idx}]")
            if type(val) is dict:
                target_keys_with_values = self.__get_key_props_with_values(val)
                act_data_similar_idx = self.__get_idx_of_similar_row(
                    target_keys_with_values, act_data
                )
                if act_data_similar_idx is None:
                    self.diff_log.missing_array_item(target_keys_with_values)
                    continue
                self.__compare_dicts(self.diff_log.curr_path, val, act_data[act_data_similar_idx])
                continue
            if type(val) is list:
                self.__try_find_list_and_compare(val, act_data[idx])
                continue
            if val != act_data[idx]:
                self.__compare_values(val, act_data[idx])

    def __try_find_list_and_compare(
        self,
        expected_val: list, 
        actual_val: int | float | str | bool | list[Any] | dict[str, Any] | None,
    ) -> None:
        if isinstance(actual_val, list):
            self.__compare_lists(self.diff_log.curr_path, expected_val, actual_val)
        elif isinstance(actual_val, str) and self.ignore_types:
            self.__try_json_decode_and_compare(expected_val,actual_val)

    def __try_find_dict_and_compare(
        self,
        expected_val: dict, 
        actual_val: int | float | str | bool | list[Any] | dict[str, Any] | None,
    ) -> None:
        if isinstance(actual_val, dict):
            self.__compare_dicts(self.diff_log.curr_path, expected_val, actual_val)
        elif isinstance(actual_val, str) and self.ignore_types:
            self.__try_json_decode_and_compare(expected_val, actual_val)

    def __check_array_lengths(self, exp_len: int, act_len: int) -> None:
        if exp_len > act_len:
            self.diff_log._lack_of_array_items(exp_len, act_len)
        elif exp_len < act_len:
            self.diff_log._exceeding_array_items(exp_len, act_len)

    def __get_key_props_with_values(
        self, object_: dict[str, Any]
    ) -> dict[str, int | float | str | bool | dict[str, Any] | list[Any] | None]:
        props_with_values = dict()
        for key in self.__match_keys:
            props_with_values[key] = object_[key]
        return props_with_values

    def __key_to_ignore(self) -> bool:
        curr_path_without_idx = (
            re.sub("\[[^()]*\]", "", self.diff_log.curr_path)
            .replace(self.right_f_name, "DATA")
            .replace(self.left_f_name, "DATA")
            .replace("////", "//")
        )
        return True if curr_path_without_idx in self.ignore else False

    @staticmethod
    def __get_idx_of_similar_row(
        keys_with_values: dict[str, int | float | str | bool | dict[str, Any] | list[Any] | None],
        data: list[dict[str, Any]],
    ) -> int | None:
        for idx, obj in enumerate(data):
            matched_props = [True for k, v in keys_with_values.items() if obj[k] == v]
            if len(matched_props) == len(keys_with_values):
                return idx
        return None

    def __compare_values(
        self,
        expected_val: int | float | str | bool | None,
        actual_val: int | float | str | bool | None,
    ) -> None:
        if expected_val == actual_val:
            return
        if not self.ignore_types:
            return self.diff_log._unequal_values(expected_val, actual_val)
        try:
            if isinstance(expected_val, int) and expected_val == int(actual_val):  # type: ignore
                return
            if isinstance(expected_val, float) and expected_val == float(actual_val):  # type: ignore
                return
            if isinstance(expected_val, str) and expected_val == str(actual_val):
                return
            if isinstance(expected_val, bool) and expected_val == bool(actual_val):
                return
        except ValueError:
            pass
        self.diff_log._unequal_values(expected_val, actual_val)
    
    def __try_json_decode_and_compare(
        self,
        expceted_val: dict[str, Any] | list[Any],
        actual_val: str,
    ) -> None:
        if isinstance(expceted_val, dict):
            try:
                parsed_val = json.loads(actual_val)
                if isinstance(parsed_val, dict):
                    self.__compare_dicts(self.diff_log.curr_path, expceted_val, parsed_val)
            except TypeError:
                self.diff_log._incorrect_type(expceted_val, actual_val)
        else:
            try:
                parsed_val = json.loads(actual_val)
                if isinstance(parsed_val, list):
                    self.__compare_lists(self.diff_log.curr_path, expceted_val, parsed_val)
            except TypeError:
                self.diff_log._incorrect_type(expceted_val, actual_val)

    def __setup_match_keys(self) -> None:
        if not self.key:
            return None
        match_keys = []
        for key in self.key:
            key_without_path = key.removeprefix(self.diff_log.curr_path + "//")
            if "//" not in key_without_path:
                match_keys.append(key_without_path)
        self.__match_keys = match_keys

    def __clear_temp_data(self) -> None:
        self.diff_log.log.clear()
        self.__match_keys.clear()
        self.diff_log.curr_path = str()
