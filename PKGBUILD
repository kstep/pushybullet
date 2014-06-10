# Maintainer: Konstantin Stepanov <me@kstep.me>
pkgname="python2-pushybullet"
pkgver="1.0"
pkgrel=1
pkgdesc="PushBullet APIv2 python bindings"
arch=('any')
url="http://github.com/kstep/pushybullet"
license=('GPL')
depends=('python2' 'python2-requests')
optdepends=('python2-websocket-client: read pushes stream in real-time')
source=(pushybullet.py pb setup.py)
md5sums=('2f2b7b1e9e8c01e334ddaad530094d21'
         '43bc45e5dd628abe5b31c5e28482c468'
         '79b695a5ebafe8ade0612d955de91e09')


build() {
    cd "$srcdir"
    python2 ./setup.py build
}

package() {
    cd "$srcdir"
    python2 ./setup.py install --root="$pkgdir" --skip-build --optimize=1
}

