#!/bin/bash
# wenshucha-site 同步:tarball 方式拉整个 repo(支持 blog/ 等子目录)
cd /tmp && rm -rf wsc-site-main wsc.tgz
curl -fsSLo wsc.tgz https://codeload.github.com/jack0752168/wenshucha-site/tar.gz/main || exit 1
tar xzf wsc.tgz || exit 1
cp -rf wsc-site-main/. /www/wwwroot/wenshucha.com/
rm -rf wsc-site-main wsc.tgz
