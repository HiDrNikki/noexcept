from pathlib import Path
packagePath = Path(__file__).parent
if packagePath.parent.name == "site-packages": userProjectPath = packagePath.parent.parent.parent.parent
else: userProjectPath = packagePath.parent
languagePath = userProjectPath / "no.language"