#!/bin/bash
# wenshucha-site 同步:tarball 方式拉整个 repo(支持 blog/ 等子目录)
# codeload 解压目录名 = <repo>-<branch> = wenshucha-site-main
cd /tmp && rm -rf wenshucha-site-main wsc.tgz
curl -fsSLo wsc.tgz https://codeload.github.com/jack0752168/wenshucha-site/tar.gz/main || exit 1
tar xzf wsc.tgz || exit 1
cp -rf wenshucha-site-main/. /www/wwwroot/wenshucha.com/
rm -rf wenshucha-site-main wsc.tgz
