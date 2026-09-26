# cn-path-fixer
诊断并修复 Windows 用户名含中文导致的开发工具异常——npm/conda 默认把全局包、缓存、虚拟环境放在中文路径下，常引发乱码、"path contains non-ASCII characters"、环境创建失败或原生编译报错。本工具先检测哪些目录落在中文路径，再支持 DryRun 预览后迁移到纯英文路径，改完自动回读校验，并支持一键回滚。仅依赖 Python 标准库，无需安装任何包。
