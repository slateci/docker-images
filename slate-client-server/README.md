# slate-client-server

This is the container that pre-installs and builds all C++ dependencies into the file system of the resulting Centos7 image for the [slateci/slate-client-server/](https://github.com/slateci/slate-client-server) project.

## Quick Try

Generate build artifacts in a project's `build/` directory using the `cmake` options described above:

```shell
[your@localmachine]$ docker run -it -v ${PWD}:/work:Z hub.opensciencegrid.org/slate/slate-client-server:1.0.1
[root@454344d8c4ca build]# cd /work/build
[root@454344d8c4ca build]# cmake3 .. -DBUILD_CLIENT=False -DBUILD_SERVER=True -DBUILD_SERVER_TESTS=True -DSTATIC_CLIENT=False
...
...
[root@454344d8c4ca build]# make
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
## Image Includes

* AWS SDK C++
* boost-devel
* cmake3
* gcc-c++.x86_64
* Helm3
* libcurl-devel
* kubectl
* make
* openssl-devel
* perl-Digest-SHA
* unzip
* which
* yaml-cpp-devel
* zlib-devel
* Docker image arguments:
  * `awssdkversion`
    * Default value is `1.7.345`
  * `helmversion`
    * Default value is `3.8.1`
  * `kubectlversion`
    * Default value is `1.21.11` 

## Examples

See [slateci/slate-client-server/](https://github.com/slateci/slate-client-server).