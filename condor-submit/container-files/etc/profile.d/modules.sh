#!/bin/bash

# sets up the modules environment for the OSG nodes - this is based on
# /cvmfs/connect.opensciencegrid.org/modules/packages/linux-rhel7-x86_64/gcc-4.8.5spack/lmod-7.8-gd44e35n2z5a6zbe54bpjtc55wrvjity/lmod/lmod/init/bash
# and also sets MODULEPATH

# no modules env for root
if [ "$EUID" -eq 0 ]; then
    return
fi

# if we don't have cvmfs mounted, then PANIC!
ls /cvmfs 2>/dev/null || return

########################################################################
# Start Lmod BASHENV
########################################################################

if [ -z "${LMOD_SH_DBG_ON+x}" ]; then
   case "$-" in
     *v*x*) __lmod_vx='vx' ;;
     *v*)   __lmod_vx='v'  ;;
     *x*)   __lmod_vx='x'  ;;
   esac;
fi

[ -n "${__lmod_vx}" ] && set +$__lmod_vx 

export LMOD_PKG=/cvmfs/connect.opensciencegrid.org/modules/packages/linux-rhel7-x86_64/gcc-4.8.5spack/lmod-7.8-gd44e35n2z5a6zbe54bpjtc55wrvjity/lmod/lmod

if [ -n "${__lmod_vx}" ]; then
    echo "Shell debugging temporarily silenced: export LMOD_SH_DBG_ON=1 for this output ($LMOD_PKG/init/bash)"
fi

export LMOD_DIR=$LMOD_PKG/libexec
export LMOD_CMD=$LMOD_PKG/libexec/lmod
export MODULESHOME=$LMOD_PKG

export LMOD_SETTARG_FULL_SUPPORT=no

########################################################################
#  Define the module command:  The first line runs the "lmod" command
#  to generate text:
#      export PATH="..."
#  then the "eval" converts the text into changes in the current shell.
#
#  The second command is the settarg command.  Normally LMOD_SETTARG_CMD
#  is undefined or is ":".  Either way the eval does nothing.  When the
#  settarg module is loaded, it defines LMOD_SETTARG_CMD.  The settarg
#  command knows how to read the ModuleTable that Lmod maintains and
#  generates a series of env. vars that describe the current state of
#  loaded modules.  So if one is on a x86_64 linux computer with gcc/4.7.2
#  and openmpi/1.6.3 loaded, then settarg will assign:
#
#     TARG=_x86_64_gcc-4.7.2_openmpi-1.6.3
#     TARG_COMPILER=gcc-4.7.2
#     TARG_COMPILER_FAMILY=gcc
#     TARG_MACH=x86_64
#     TARG_MPI=openmpi-1.6.3
#     TARG_MPI_FAMILY=openmpi
#     TARG_SUMMARY=x86_64_gcc-4.7.2_openmpi-1.6.3
#     TARG_TITLE_BAR=gcc-4.7.2 O-1.6.3
#     TARG_TITLE_BAR_PAREN=(gcc-4.7.2 O-1.6.3)
#
#  unloading openmpi/1.6.3 automatically changes these vars to be:
#
#     TARG=_x86_64_gcc-4.6.3
#     TARG_COMPILER=gcc-4.6.3
#     TARG_COMPILER_FAMILY=gcc
#     TARG_MACH=x86_64
#     TARG_SUMMARY=x86_64_gcc-4.6.3
#     TARG_TITLE_BAR=gcc-4.6.3
#     TARG_TITLE_BAR_PAREN=(gcc-4.6.3)
#
# See Lmod web site for more details.


if [ "no" = "no" ]; then
   module()
   {
     eval $($LMOD_CMD bash "$@") && eval $(${LMOD_SETTARG_CMD:-:} -s sh)
   }
else
   module()
   {
     ############################################################
     # Silence shell debug UNLESS $LMOD_SH_DBG_ON has a value
     if [ -z "${LMOD_SH_DBG_ON+x}" ]; then
        case "$-" in
          *v*x*) __lmod_sh_dbg='vx' ;;
          *v*)   __lmod_sh_dbg='v'  ;;
          *x*)   __lmod_sh_dbg='x'  ;;
        esac;
     fi
     
     if [ -n "${__lmod_sh_dbg}" ]; then
        set +$__lmod_sh_dbg 
        echo "Shell debugging temporarily silenced: export LMOD_SH_DBG_ON=1 for Lmod's output"
     fi

     eval $($LMOD_CMD bash "$@") && eval $(${LMOD_SETTARG_CMD:-:} -s sh)
     local _lmod_my_status=$?

     ############################################################
     # Un-silence shell debug after module command
     if [ -n "${__lmod_sh_dbg:-}" ]; then
       echo "Shell debugging restarted"
       set -$__lmod_sh_dbg;
       unset __lmod_sh_dbg;
     fi;
     return $_lmod_my_status
   }
fi


LMOD_VERSION="7.8"
export LMOD_VERSION

if [ "${LMOD_SETTARG_CMD:-:}" != ":" ]; then
  settarg () {
    eval $(${LMOD_SETTARG_CMD:-:} -s sh "$@" )
  }
fi


########################################################################
#  ml is a shorthand tool for people who can't type moduel, err, module
#  It is also a combination command:
#     ml            -> module list
#     ml gcc        -> module load gcc
#     ml -gcc intel -> module unload gcc; module load intel
#  It does much more do: "ml --help" for more information.


unalias ml 2> /dev/null || true
ml()
{
  eval $($LMOD_DIR/ml_cmd "$@")
}

if [ -n "${BASH_VERSION:-}" -a "yes" != no ]; then
  export -f module
  export -f ml
fi
unset export_module

########################################################################
#  clearMT removes the ModuleTable from your environment.  It is rarely
#  needed but it useful sometimes.

clearMT()
{
  eval $($LMOD_DIR/clearMT_cmd bash)
}

xSetTitleLmod()
{
  builtin echo -n -e "\033]2;$1\007";
}

########################################################################
#  Make tab completions available to bash users.

# disabled to improve login times
#if [ ${BASH_VERSINFO:-0} -ge 3 ] && [ -r  /cvmfs/connect.opensciencegrid.org/modules/packages/linux-rhel7-x86_64/gcc-4.8.5spack/lmod-7.8-gd44e35n2z5a6zbe54bpjtc55wrvjity/lmod/lmod/init/lmod_bash_completions ] && [ -n "${PS1:-}" ]; then
# . /cvmfs/connect.opensciencegrid.org/modules/packages/linux-rhel7-x86_64/gcc-4.8.5spack/lmod-7.8-gd44e35n2z5a6zbe54bpjtc55wrvjity/lmod/lmod/init/lmod_bash_completions
#fi


# Restoring XTRACE and VERBOSE states.
if [ -n "${__lmod_vx:-}" ]; then
  echo "Shell debugging restarted"
  set -$__lmod_vx;
  unset __lmod_vx;
fi;

########################################################################
# End Lmod BASHENV
########################################################################
#

export MODULEPATH=/cvmfs/connect.opensciencegrid.org/modules/modulefiles/linux-rhel7-x86_64/Core




