English | [中文](README_ZH.md)

# Digital Asset Pipeline (DAP)

This project is a pipeline for organizing and managing digital assets. It allows users to specify target directories and rules for filtering files based on various attributes such as format, user, group, permissions, and regex patterns for file names and paths. Note that **Python 3.11 or higher** is required.

> [!WARNING]
> This project is unavailable on Windows. 

**Usage:**
1. Clone the repository
```bash
git clone https://github.com/Haozhe-py/dap.git
```

2. Run the pipeline
```bash
sudo python dap/src/main.py --config PATH_TO_CONFIG_FILE --output PATH_TO_OUTPUT_DIRECTORY
```
Root permission is required as some of the directories may require elevated privileges to access. **If you don't want to use root permission, ensure that the directories you are accessing have the appropriate permissions set.**

The generated manifest files will be saved in the specified output directory.

**Structure of config file:**
```json
{
    "target_dirs": [
        "PATH_TO_DIRECTORY_1",
        "PATH_TO_DIRECTORY_2",
        "PATH_TO_DIRECTORY_3"
    ],
    "rules": [
        {
            "fmt": "fmt1",
            "user": "user1",
            "group": "group1",
            "perm": "perm1",
            "regex_p_file": "regex_f_1",
            "regex_p_path": "regex_p_1",
            "file_group_name": "file_group_name_1"
        },
        {
            "fmt": "fmt2",
            "user": "user2",
            "group": "group2",
            "perm": "perm2",
            "regex_p_file": "regex_f_2",
            "regex_p_path": "regex_p_2",
            "file_group_name": "file_group_name_2"
        }
    ]
}
```
Note that when specifying the `rules` section, you can use the following values if you want a rule do not filter by a specific attribute:
- `"fmt"`: `""` (empty string) means no filtering by format
- `"user"`: `""` or `null` means no filtering by user
- `"group"`: `""` or `null` means no filtering by group
- `"perm"`: `"000"` means no filtering by permission
- `"regex_p_file"`: `".*"` means no filtering by file name
- `"regex_p_path"`: `".*"` means no filtering by path

A default set of rules is provided. If you want to use the default rules, you can remove the `rules` section from the config file. The default rules are defined in `src/match.py`.
