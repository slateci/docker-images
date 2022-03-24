# slate-client-server

This is the container that pre-installs and builds all C++ dependencies into the file system of the resulting Centos7 image for the [slateci/slate-client-server/](https://github.com/slateci/slate-client-server) project.

## Quick Try

Generate build artifacts in a project's `build/` directory using the `cmake` options described above:

```shell
[your@localmachine]$ docker run -it -v <project-dir>:/work:Z --env CMAKE_OPTS="-DBUILD_CLIENT=False -DBUILD_SERVER=True -DBUILD_SERVER_TESTS=True -DSTATIC_CLIENT=False" hub.opensciencegrid.org/slate/slate-client-server:1.0.0
Building the slate server...
CMake Warning (dev) in CMakeLists.txt:
  No project() command is present.  The top-level CMakeLists.txt file must
  contain a literal, direct call to the project() command.  Add a line of
  code such as

    project(ProjectName)

  near the top of the file, but after cmake_minimum_required().

  CMake is pretending there is a "project(Project)" command on the first
  line.
This warning is for project developers.  Use -Wno-dev to suppress it.

Will build client
Will build server
Will build server tests
-- Found libcrypto:  (found version "1.0.2k")
-- Found ssl:  (found version "1.0.2k")
-- Found yaml-cpp: /usr (found version "0.5.1")
-- Configuring done
-- Generating done
-- Build files have been written to: /work/build
[  1%] Generating server_version.h, server_version.h_
[  1%] Generating client_version.h, client_version.h_
[  1%] Built target embed_version
Scanning dependencies of target slate-server
[  2%] Building CXX object CMakeFiles/slate-server.dir/src/slate_service.cpp.o
...
...
[ 99%] Building CXX object CMakeFiles/test-instance-deletion.dir/test/TestInstanceDeletion.cpp.o
[100%] Linking CXX executable tests/test-instance-deletion
[100%] Built target test-instance-deletion
```

Alternatively run a shell in the container and execute `make` yourself:

```shell
[your@localmachine]$ docker run -it -v ${PWD}:/work:Z --env CMAKE_OPTS="-DBUILD_CLIENT=False -DBUILD_SERVER=True -DBUILD_SERVER_TESTS=True -DSTATIC_CLIENT=False" slate-client-server:maker bash
[root@454344d8c4ca build]# make
...
...
```
## Image Includes

* boost-devel
* cmake3
* gcc-c++.x86_64
* git
* libcurl-devel
* make
* openssl-devel
* yaml-cpp-devel
* zlib-devel
* AWS SDK C++
* Docker environmental variables:
  * `DEBUG`
    * Default value is `False`
* Docker image arguments:
  * `awssdkversion`
    * Default value is `'1.7.345'`

## Examples

See [slateci/slate-client-server/](https://github.com/slateci/slate-client-server).