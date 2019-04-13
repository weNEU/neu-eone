# neu-eone
A spider can login NEU eone(一网通办) system
## Python version
3+
## Library you need
* requests
## How to use
### Import
Put the file "eone.py" in you project and import it in you project
### Use
You can use the function "login" to check if the student id and password are correct.
For example if you import the file use "import eone",you can use the login function as "eone.login(stu_id,stu_passwd)", if function return 1, the id and password are correct while return 0 means id or passwd are uncorrect.
