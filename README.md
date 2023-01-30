# json-compare
Json-compare is a simple package that allows you to easily and fastly compare two .json files.

[![made-with-python](https://img.shields.io/badge/python-3.10%2B-brightgreen)](https://www.python.org/)

Usage
---
Compare files just as they are:

```python
from json_compare import JSONComparator

comparator = JSONComparator(
    left_file_path="expected.json",
    right_file_path="actual.json",
)

# compare "actual.json" from the perspective of "expected.json"'s structure
comparator.compare_with_right()  # / compare_with_left() / full_compare()

# save diff logs to ".comparison_logs" folder
comparator.save_diff_logs(path="comparison_logs")

# or just print them into stdout
diffs = comparator.diff_log.log
print("\n".join(diffs))
```
Set key property to perform more accurate comparisons of objects in arrays:

```python
# expected.json: {"cats": [{"id": 4, "name": "Nyan"}, {"id": 2, "name": "Marx"}, {"id": 8, "name": "Flake"}]}
# actual.json: {"cats": [{"id": 2, "name": "Marx"}, {"id": 4, "name": "Naan"}]}

comparator = JSONComparator(
    left_file_path="expected.json",
    right_file_path="actual.json",
    target_property="DATA.cats.<array>.id",  # just pass a "path" to needed property with following keywords: 
)                                            # DATA - points to the root of file 
                                             # <array> - indicates array with key property's object
```
In this case, saved diff log would look like that:
```text
RIGHT.cats.<array>
lack of items in array: expected 3 items, got only 2
RIGHT.cats.<array[0]>.name
unequal values: expected "Nyan", got "Naan" instead
RIGHT.cats.<array[2]>
missing array item: expected <object> with "id"=8
```
You can go further and add some `properties_to_ignore` to your comparator:
```python
# expected.json: [{"id": 4, "name": "Nyan", "age": 2}, {"id": 2, "name": "Marx", "age": 7}, {"id": 8, "name": "Flake", "age": 4}]
# actual.json: [{"id": 2, "name": "Marx", "age": 7}, {"id": 4, "name": "Naan", "age": "two"}, {"id": 9, "name": "Lol", "age": 1}]

comparator = JSONComparator(
    left_file_path="expected.json",
    right_file_path="actual.json",
    target_property="DATA.<array>.id",
    properties_to_ignore=["DATA.<array>.age"]
)  
```
And here the result:
```text
RIGHT.<array[0]>.name
unequal values: expected "Nyan", got "Naan" instead
RIGHT.<array[2]>
missing array item: expected <object> with "id"=8
```