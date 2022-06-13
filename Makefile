.DEFAULT_GOAL := build

SYSTEM := $(shell uname -s)
ARCH   := $(shell uname -m)

LLVM_VERSION 	= 14.0.4

ifeq ($(LLVM_SYS),)
	BUILD_LLVM = 1
	LLVM_SYS_130_PREFIX := $(HOME)/llvm-$(LLVM_VERSION)
else
	BUILD_LLVM = 0
	LLVM_SYS_130_PREFIX := $(LLVM_SYS)
endif

CLANG_BIN=$(LLVM_SYS_130_PREFIX)/bin/clang

ifeq ($(SYSTEM), Darwin)
	CFLAGS="-I`brew --prefix gmp`/include -I`brew --prefix libsecp256k1`/include"
	LDFLAGS="-L`brew --prefix gmp`/lib -L`brew --prefix libsecp256k1`/lib"
else
	CFLAGS=
	LDFLAGS=
endif

llvm_project:
	
	# build llvm 
	@if [ $(BUILD_LLVM) = 1 ] && [ $(SYSTEM) = "Darwin" ]; then\
		brew install cmake ninja;\
	elif [ $(BUILD_LLVM) = 1 ]; then\
		apt-get install -y cmake ninja;\
    fi

	@if [ $(BUILD_LLVM) = 1 ]; then\
		git clone https://github.com/llvm/llvm-project -b llvmorg-$(LLVM_VERSION);\
		cd llvm-project/ && mkdir -p build && cd build && cmake -DLLVM_ENABLE_PROJECTS='clang;compiler-rt' -G "Unix Makefiles" -DCMAKE_INSTALL_PREFIX=$(LLVM_SYS_130_PREFIX)/ ../llvm && cmake --build . --target install;\
	fi

build: llvm_project
	# install chinfuzz
	CFLAGS=$(CFLAGS) LDFLAGS=$(LDFLAGS) CLANG_BIN=$(CLANG_BIN) pip3 install . -U
