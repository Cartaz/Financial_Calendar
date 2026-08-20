# Maintainer: User <user@example.com>
pkgname=financial_calendar
pkgver=1.0.0
pkgrel=1
pkgdesc="Visualizzatore di calendari economici IG e FXStreet per KDE Plasma"
arch=('any')
url="https://github.com/user/financial_calendar"
license=('MIT')
depends=('python>=3.12' 'pyside6>=6.6.0' 'python-requests>=2.31.0')
source=("$pkgname-$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    install -d "$pkgdir/opt/$pkgname"
    cp -r "$srcdir/$pkgname-$pkgver/"* "$pkgdir/opt/$pkgname/"

    install -d "$pkgdir/usr/bin"
    cat > "$pkgdir/usr/bin/financial-calendar" << EOF
#!/usr/bin/env bash
exec /opt/$pkgname/.venv/bin/python /opt/$pkgname/main.py "\$@"
EOF
    chmod 755 "$pkgdir/usr/bin/financial-calendar"

    install -d "$pkgdir/usr/share/applications"
    cat > "$pkgdir/usr/share/applications/financial_calendar.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Calendario Finanziario
Comment=Visualizzatore di calendari economici IG e FXStreet
Exec=/usr/bin/financial-calendar %f
Icon=financial-calendar
Terminal=false
Categories=Office;Finance;
Keywords=finance;calendar;economic;forex;
StartupNotify=true
EOF

    install -Dm644 "$srcdir/$pkgname-$pkgver/assets/icons/financial-calendar.png" \
        "$pkgdir/usr/share/icons/hicolor/256x256/apps/financial-calendar.png"
}
