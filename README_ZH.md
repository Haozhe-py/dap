中文 | [English](README.md)

# 数字资源处理系统 （Digital Asset Pipeline, DAP）

此项目是一个用于组织和管理数字资源的处理系统。它允许用户指定目标目录和规则，根据各种属性（如格式、用户、组、权限以及文件名和路径的正则表达式模式）过滤文件。请注意，**需要 Python 3.11 或更高版本**。

> [!WARNING]
> 此项目在 Windows 上不可用。

**使用方法：**
1. 克隆仓库
```bash
git clone https://github.com/Haozhe-py/dap.git
```

2. 运行处理系统
```bash
sudo python dap/src/main.py --config PATH_TO_CONFIG_FILE --output PATH_TO_OUTPUT_DIRECTORY
```
由于某些目录可能需要提升权限才能访问，因此需要 root 权限。**如果您不想使用 root 权限，请确保您访问的目录具有适当的权限设置。**

生成的清单文件将保存在指定的输出目录中。

**配置文件结构：**
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
请注意，在指定 `rules` 部分时，如果您希望某个规则不按特定属性进行过滤，可以使用以下值：
- `"fmt"`: `""`（空字符串）表示不按格式过滤
- `"user"`: `""` 或 `null` 表示不按用户过滤
- `"group"`: `""` 或 `null` 表示不按组过滤
- `"perm"`: `"000"` 表示不按权限过滤
- `"regex_p_file"`: `".*"` 表示不按文件名过滤
- `"regex_p_path"`: `".*"` 表示不按路径过滤

此项目提供了一组默认规则。如果您希望使用默认规则，可以从配置文件中删除 `rules` 部分。默认规则定义在 `src/match.py` 中。
