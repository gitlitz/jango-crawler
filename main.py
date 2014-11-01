import os
import re
import json
import html

from mutagen.easymp4 import EasyMP4
from mutagen.id3 import ID3, APIC, error

from mutagen.mp3 import MP3
from mutagen.mp4 import MP4Cover
import mutagen
import requests
from mutagen.easyid3 import EasyID3, mutagen


tags_url = 'http://www.jango.com/players/usd'
stream_url_format = 'http://www.jango.com/streams/{}'


# 113280941
# 321275470
def main():
    station_id = 113280941
    stream_url = stream_url_format.format(station_id)
    cookies = ''
    for i in range(100):
        stream_request = requests.get(stream_url, cookies=cookies)
        cookies = stream_request.cookies
        stream_content = stream_request.content
        mp3_url = json.loads(stream_content.decode('utf-8'))['url']

        tags_request = requests.get(tags_url, cookies=cookies)
        tags_content = html.unescape(tags_request.content.decode('utf-8'))
        tags = json.loads(re.findall('.*\n_jm.song_info = (.+);\n', tags_content)[0])

        picture_url = 'http:' + re.findall("id='player_main_pic_img' alt='' title='' style='display:none;' src='(.*)'",
                                           tags_content)[0]

        picture = requests.get(picture_url).content
        artist = tags['artist'].replace('/', '&')
        song_name = tags['song']
        genre = tags['genre']
        album = re.findall(u'on</span> (.*)</div>\\\\n</div>', tags_content)[0]

        if not os.path.exists(artist):
            os.mkdir(artist)

        output_path = os.path.join(artist, artist + ' - ' + song_name + os.path.splitext(mp3_url)[1])

        if os.path.exists(output_path):
            print('skipped:', output_path)
            continue

        mp3 = requests.get(mp3_url).content

        f = open(output_path, 'wb')
        f.write(mp3)
        f.close()
        print('added:', output_path)

        try:
            audio_file = EasyMP4(output_path)

            audio_file['artist'] = artist
            audio_file['album'] = album
            audio_file['title'] = song_name
            audio_file['genre'] = genre
            audio_file['cover'] = [MP4Cover(picture)]
            audio_file.save()
        except mutagen.mp4.error:
            audio = MP3(output_path, ID3=ID3)
            try:
                audio.add_tags()
            except error:
                pass

            audio.tags.add(
                APIC(
                    encoding=3,  # 3 is for utf-8
                    mime='image/jpeg',  # image/jpeg or image/png
                    type=3,  # 3 is for the cover image
                    desc=u'Cover',
                    data=picture
                )
            )
            audio.save()

            audio_file = EasyID3(output_path)

            audio_file['artist'] = artist
            audio_file['genre'] = genre
            audio_file['album'] = album
            audio_file['title'] = song_name
            audio_file.save()


if __name__ == '__main__':
    main()
