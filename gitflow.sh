#!/bin/bash
# ******************
# for git flow 
# ******************

set -e 

# ****************************************** for easy use, see shellful.sh
has () {
        local item=$1; shift
        echo $@ | grep -wq $item
        }

red=`tput setaf 1`
green=`tput setaf 2`
yellow=`tput setaf 3`
white=`tput setaf 7`

warn () {
    echo -e "${red} $@${white}"
}

ok () {
    echo -e "${green} $@${white}"
}

info () {
    echo -e "${white} $@"
}

notice () {
    echo -e "${yellow} $@${white}"
}

die () {
    warn "$@"; exit 1;
}
# ****************************************** 

AVAILABLE_COMMAND=(start switch track finish)
SCRIPT=$0

usage () {
    notice "Usage: `basename $SCRIPT` [OPTIONS] COMMAND BRANCH "
    notice "Options:"
    notice "  -p          \t默认是./, 指定操作的项目的路径"
    info
    notice "Commands:"
    notice "  start       \t创建分支"
    notice "  switch      \t切换分支"
    notice "  track       \t跟踪远程分支"
    notice "  finish      \t结束分支"
    exit 1
}

while getopts 'p:' OPT;
do
    case $OPT in
        p)
            PROJECT_PATH="$OPTARG";;
        ?)
            usage
    esac
done

shift $((OPTIND - 1))

if [[ $# -ne 2 ]]
then
    warn "参数个数不对"
    usage
fi


COMMAND=$1
if ! has $COMMAND ${AVAILABLE_COMMAND[@]}
then
    warn "不支持的命令"
    usage
fi

BRANCH=$2
BRANCH=(`echo "$BRANCH" | sed 's/\// /g'`)
BRANCH_TYPE=${BRANCH[0]}
BRANCH_NAME=${BRANCH[1]}
PROJECT_PATH=${PROJECT_PATH:-`pwd`}
cd $PROJECT_PATH
PROJECT_PATH=`pwd`

notice "project_path: $PROJECT_PATH, command: $COMMAND, branch: $BRANCH"
info

gitflow_switch () {
    # switch to specify branch of project
    test $BRANCH_NAME && branch=$BRANCH_TYPE/$BRANCH_NAME || branch=$BRANCH_TYPE
    if echo "`git branch`" | grep -wq "$branch"
    then
        info "branch $branch exists, switch to "
        git checkout $branch
    else
        notice 'branch not exists, try track remote'
        gitflow_track $branch
    fi
}

gitflow_track () {
    # track remote branch 
    notice "track remote $BRANCH_TYPE/$BRANCH_NAME"
    git flow $BRANCH_TYPE track $BRANCH_NAME
}

update_develop () {
    notice "sync master to remote, develop to master"
    git pull origin master:master
    git checkout develop
    git rebase master
}

gitflow_start_feature () {
    notice 'start new feature branch'
    test $BRANCH_NAME || die "please provide branch_name in format: feature/xxx"
    update_develop
    git flow feature start $BRANCH_NAME
}

gitflow_start_release () {
    # assume version was bumped up before start release branch, no need to bump version up
    # 不支持给出参数来建立release分支，是为了强制写CHANGES.md
    # 版本号只会自动的去CHANGES.md取最新的版本号作为要建立的版本
    #if echo $BRANCH_NAME | grep -E '[0-9]+.[0-9]+.[0-9]+'
    #then
    #    info "use given version num $BRANCH_NAME"
    #    new_version=$BRANCH_NAME
    #else
    #    new_version=$(sed -nE '/[0-9]+.[0-9]+.[0-9]+/p' CHANGES.md | head -n 1 | cut -d ' ' -f 3)
    #    info "use news CHANGES.md version num $new_version"
    #    # assume version was bumped up before start release branch, no need to bump version up
    #    #version=$(sed -nE '/[0-9]+.[0-9]+.[0-9]+/p' CHANGES.md | head -n 1 | cut -d ' ' -f 3)
    #    #version=(`echo "$version" | sed 's/\./ /g'`)
    #    #last_num=${version[2]}
    #    #new_version="${version[0]}.${version[1]}.$((last_num + 1))"
    #fi
    test -e ./CHANGES.md || die "no CHANGES.md in the $PROJECT_PATH"
    update_develop
    new_version=$(sed -nE '/[0-9]+.[0-9]+.[0-9]+/p' CHANGES.md | head -n 1 | cut -d ' ' -f 3)
    notice "use news CHANGES.md version num $new_version"
    notice "start new release/$new_version"
    git flow release start $new_version
    notice "publish new release/$new_version"
    git flow release publish $new_version
}

gitflow_start () {
    if ! has $BRANCH_TYPE "feature release"
    then
        die "COMMAND start not support branch_type: $BRANCH_TYPE"
    fi

    gitflow_start_$BRANCH_TYPE
}

gitflow_finish_feature () {
    notice "finish feature/$BRANCH_NAME "
    git flow feature finish $BRANCH_NAME
}

gitflow_finish_release () {
    if echo $BRANCH_NAME | grep -E '[0-9]+.[0-9]+.[0-9]+'
    then
        notice "use given version num $BRANCH_NAME"
        version=$BRANCH_NAME
    else
        test -e ./CHANGES.md || die "no CHANGES.md in the $PROJECT_PATH"
        version=$(sed -nE '/[0-9]+.[0-9]+.[0-9]+/p' CHANGES.md | head -n 1 | cut -d ' ' -f 3)
        notice "use news CHANGES.md version num $version"
    fi
 
    notice "push release/$version to remote"
    git push origin release/$version
    notice "finish release/$version"
    git flow release finish $version
    notice "sync master branch"
    git checkout master
    git push origin master
    git push origin $version
    git checkout develop
    git rebase master
}

gitflow_finish () {
    gitflow_finish_$BRANCH_TYPE
}

gitflow_$COMMAND
