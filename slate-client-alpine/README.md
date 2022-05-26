# slate-client-alpine

This is the container that provides a build environment for the slateci/slate-client-server project and the static Linux SLATE Remote Client.

## Quick Try

```shell
[your@localmachine]$ docker run -it -v ${PWD}:/work:Z hub.opensciencegrid.org/slate/slate-client-alpine:1.0.0
[root@454344d8c4ca build]# cd /work/build
[root@454344d8c4ca build]# cmake .. -DBUILD_CLIENT=True -DBUILD_SERVER=False -DBUILD_SERVER_TESTS=False -DSTATIC_CLIENT=True
...
...
[root@454344d8c4ca build]# make
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
-- Found libcrypto: /usr/lib (found version "1.1.1o")
-- Found ssl: /usr/lib (found version "1.1.1o")
Attempting fully static link
-- Configuring done
-- Generating done
-- Build files have been written to: /work/build
/work/build # make
[  3%] Generating client_version.h, client_version.h_
[  3%] Built target embed_version
Consolidate compiler generated dependencies of target slate
[  7%] Building CXX object CMakeFiles/slate.dir/src/client/Client.cpp.o
...
...
```

## Image Includes

* cmake
* curl-dev
* curl-static
* gcc
* g++
* libc-dev
* libssh2-dev
* make
* musl-dev
* nghttp2-dev
* nghttp2-static
* openssl-dev
* zlib-dev

## Examples

See [slateci/slate-client-server/](https://github.com/slateci/slate-client-server).