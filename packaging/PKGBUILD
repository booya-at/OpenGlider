# Maintainer: Simon Klemenc <simon@booya.at>
project_name=openglider
pkgname=openglider-git
pkgver=0.1
pkgrel=1
pkgdesc="A Python lib for Paraglider-engineering"
arch=('any')
url="https://github.com/hiaselhans/OpenGlider"
license=('GPL3')
depends=('python-ezodf-git' 'dxfwrite' 'python2-scipy' 'vtk' 'python2-svgwrite' 'python2-matplotlib')
makedepends=('git' 'python2' 'python2-setuptools')
conflicts=()
source=("$pkgname"::'git://github.com/hiaselhans/OpenGlider')
# Because the sources are not static, skip Git checksum:
md5sums=('SKIP')

pkgver() {
  cd "$srcdir/$pkgname"
  git describe --long --tags | sed -E 's/([^-]*-g)/r\1/;s/-/./g'
}
package() {
  cd "$srcdir/$pkgname"
  python2 setup.py install --root="$pkgdir/"
}

