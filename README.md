ezMake
=========
ezMake is an easy to use automated builder based on special make files.
You can define different targets and target dependencies.

The make file is assumed to be named ezMakefile.

The ezMakefile
--------------
The ezMakefile is a simple text file preferably  UTF-8 coded.

### Using comments
Each line starting with a hash is interpreted as a comment:

    # Makefile for project X

### Defining a target
A target is defined by a line starting with a right arrow:

    # Makefile for project X
    
    # Install target
    > install
    
### Defining actions
An action is a build in command or just executing an external process.
Normally actions should be defined inside targets. Actions inside of targets 
have to be indented by at least one space character or a tab.
For common operations actions outside of targets can be defined:

    # Makefile for project X
    # An action which is executed every time ezmake is run
    get git_tag
    
    # Install target
    > install
        # An actions inside of a target
        cp a/c.tct b/

### Using dependencies
If needing dependencies just add them after a second right arrow after the target name:

    # Makefile for project X
    # An action which is executed every time ezmake is run
    get git_tag
    
    # Install target depending on build
    > install > build
        # An actions inside of a target
        cp a/c.tct b/
        
    # The build target
    > build
        python setup.py
    
The order of targets does not matter and each target is run only once.

Theres a special target *all* which is called when no other target is explicitly named  on the commandline.
If you want to run *build* when no target is specified:

    ...
    > all > build
    ...
    
A target can depend on more than one other targets:

    ...
    # Install depends on build and version
    > install > build version
    ...

### Use variables
You can use variables. Currently there is only {target} which is substituted by the current target name.
Other variables can be generated if you use internal get commands (see below).

    ...
    > version.py
        do write {target} VERSION = '{git_tag}'
    ...

### Using builtin commands
There are several internal command which are prefixed by *do*, *get* or *set*.

#### Set command
With set, you can set internal variables.

    ...
    set var Test
    set var1 {var}-{git_tag}
    ...

#### Get commands
Get commands store information in a variable named like the command 
* git_tag: Stores the last git tag
* git_branch: Stores the current git branch name or '' if on master
* git_modified: stores 'Modified' if working copy contains uncommitted changes or '' otherwise 

Example:

    ...
    get git_tag
    ...

#### Do commands
Do commands executes simple things
* write *file* *text*: Writes the text to a file
* append *file* *text*: Appends the text to a file
* print *text*: Just prints something
* rm *file*: Removes a file (supports wildcards)
* cd *path*: Changes to the directory
* mkdir *path*: Creates a directory
* rmdir *path*: Removes a directory

Example:

    ...
    do write version.py VERSION = 'v1.0'
    do append version.py BRANCH = 'FunctionX'
    ...

Command line
------------
ezMake automatically uses *ezMakefile* if no other file is specified and runs target all 
(and the target it depends on).

    ezmake [-f MAKEFILE] [TARGET]

License
-------
Andreas Schawo <andreas@schawo.de>, (c) 2021

This work is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
