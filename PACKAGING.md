# Packaging

## Debian Installation

### Prepare

```
$ ln -s packaging/debian
```

### Install

```
$ sudo apt install build-essential devscripts equivs
```

### Install Dependencies

```
$ sudo mk-build-deps -i
$ sudo apt remove gerrit-checks-mock-fetch-endpoint-build-deps
```

### Build

```
$ debuild -b -uc -us -i
```

### Release

Due to `deb` magics, before release version must be updated manually in `packaging/debian/changelog`.

### Install Manually

```
$ dpkg -i ../gerrit-checks-mock-fetch-endpoint*.deb
```
