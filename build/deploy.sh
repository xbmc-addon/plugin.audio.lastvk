cd `dirname $0`/../src

OLD=`cat ./addon.xml | grep '<addon' | grep 'version="' | grep -E -o 'version="[0-9\.]+"' |  grep -E -o '[0-9\.]+'`
echo "Old version: $OLD"
echo -n 'New version: '
read NEW

sed -e "s/Last\.VK\" version=\"$OLD\"/Last\.VK\" version=\"$NEW\"/g" ./addon.xml > ./addon2.xml
mv ./addon2.xml ./addon.xml

rm -rf ../plugin.audio.lastvk
rm -f ./plugin.audio.lastvk.zip
mkdir ../plugin.audio.lastvk
cp -r ./* ../plugin.audio.lastvk/

cd ../
zip -rq ./plugin.audio.lastvk.zip ./plugin.audio.lastvk

cp ./plugin.audio.lastvk.zip ../repository.hal9000/repo/plugin.audio.lastvk/plugin.audio.lastvk-$NEW.zip

rm -rf ./plugin.audio.lastvk
rm -f ./plugin.audio.lastvk.zip

`../repository.hal9000/build/build.sh`
