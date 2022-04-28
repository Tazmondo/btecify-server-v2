import asyncio
from logging import Logger
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4 as makeUUID

from yt_dlp import YoutubeDL as Extractinator

import app.schemas as schemas

locallogger = Logger("yt-dl logger", 100000)  # So that stdout isnt spammed by yt-dl

extractDir = Path('./extractions')
if not extractDir.exists():
    extractDir.mkdir()

[x.unlink() for x in extractDir.iterdir()]  # Remove any existing files


def readData(file: Path) -> bytes:
    with file.open("rb") as f:
        filedata = f.read()

    file.unlink()
    return filedata


def extract(options, url):
    with Extractinator(options) as downloader:
        info = downloader.extract_info(url)
    return info


def extractInfo(options, url):
    with Extractinator(options) as downloader:
        info = downloader.extract_info(url, download=False)
    return info


async def downloadSong(url: str) -> schemas.SongDownload:
    loop = asyncio.get_event_loop()

    uuid = str(makeUUID())  # Use uuid to prevent any name collisions with multiple downloads at once
    options = {
        "noplaylist": True,
        "playlistend": 0,  # Ensures that playlists aren't downloaded
        "format": "worstaudio",
        "outtmpl": f'./extractions/{uuid}',
        "writethumbnail": True,
        # "quiet": True,
        # "no_warnings": True,
        # "logger": locallogger
    }

    info = await loop.run_in_executor(None, extract, options, url)

    file = Path(info['requested_downloads'][0]['filepath'])
    thumbfile = Path(info['thumbnails'][-1]['filepath'])

    if info.get('_type') == "playlist":
        file.unlink()
        thumbfile.unlink()
        raise ValueError("Playlist url provided.")

    try:  # Read music data
        filedata = readData(file)
        pass
    except FileNotFoundError:
        filedata = None

    try:  # Read music data
        thumbdata = readData(thumbfile)
        pass
    except FileNotFoundError:
        thumbdata = None

    return schemas.SongDownload(
        data=filedata,
        dataext=info['ext'],
        thumbdata=thumbdata,
        thumbext=Path(urlparse(info['thumbnail']).path).suffix[1:],  # Get extension from web url, with period removed
        info=info,
        extractor=info['extractor_key']
    )


# Perhaps take a progress callback parameter, so progress can be updated as it downloads large playlists.
async def downloadPlaylist(url: str) -> schemas.PlaylistDownload:
    uuid = str(makeUUID())

    options = {
        "format": "worstaudio",
        "quiet": True,
        "no_warnings": True,
        "logger": locallogger
    }

    pass


if __name__ == "__main__":
    options = {
        "format": "worstaudio",
    }

    testurlregvideo = "youtube.com/watch?v=cxFFhUvlRiM"
    testurlmusicvideo = "https://www.youtube.com/watch?v=T5-faDLv1Vs"
    testurlbandcamp = "https://abductedbysharks.bandcamp.com/track/hammerhead"

    testurlytplaylist = "https://www.youtube.com/playlist?list=PL22baOOM5dLdXrvuaxtquOQnnzB8mW6JB"
    testurlytalbum = "https://www.youtube.com/playlist?list=OLAK5uy_nafOyxSwDvUta0pkBIkQfpUV6qKZ1jQaw"

    # Same as regular album
    testurlytmusicalbum = "https://music.youtube.com/playlist?list=OLAK5uy_nafOyxSwDvUta0pkBIkQfpUV6qKZ1jQaw"

    testurlbandcampalbum = "https://abductedbysharks.bandcamp.com/album/abducted-by-sharks"
    testurlbandcampallalbums = "https://abductedbysharks.bandcamp.com/"

    # extractInfo(options, testurlbandcampalbum)

    print("done")


    # async def start():
    #     x = await downloadSong(testurlmusicvideo)
    #     print(x)

    async def start():
        loop = asyncio.get_event_loop()

        results = await asyncio.gather(
            *[loop.run_in_executor(None, extractInfo, options, url)
              for url in
              [testurlytalbum, testurlytmusicalbum, testurlbandcampalbum]
              ],
            return_exceptions=True
        )

        print("done")


    asyncio.run(start())

"""
Available options:
    username:          Username for authentication purposes.
    password:          Password for authentication purposes.
    videopassword:     Password for accessing a video.
    ap_mso:            Adobe Pass multiple-system operator identifier.
    ap_username:       Multiple-system operator account username.
    ap_password:       Multiple-system operator account password.
    usenetrc:          Use netrc for authentication instead.
    verbose:           Print additional info to stdout.
    quiet:             Do not print messages to stdout.
    no_warnings:       Do not print out anything for warnings.
    forceurl:          Force printing final URL.
    forcetitle:        Force printing title.
    forceid:           Force printing ID.
    forcethumbnail:    Force printing thumbnail URL.
    forcedescription:  Force printing description.
    forcefilename:     Force printing final filename.
    forceduration:     Force printing duration.
    forcejson:         Force printing info_dict as JSON.
    dump_single_json:  Force printing the info_dict of the whole playlist
                       (or video) as a single JSON line.
    simulate:          Do not download the video files.
    format:            Video format code. See options.py for more information.
    outtmpl:           Template for output names.
    restrictfilenames: Do not allow "&" and spaces in file names
    ignoreerrors:      Do not stop on download errors.
    force_generic_extractor: Force downloader to use the generic extractor
    nooverwrites:      Prevent overwriting files.
    playliststart:     Playlist item to start at.
    playlistend:       Playlist item to end at.
    playlist_items:    Specific indices of playlist to download.
    playlistreverse:   Download playlist items in reverse order.
    playlistrandom:    Download playlist items in random order.
    matchtitle:        Download only matching titles.
    rejecttitle:       Reject downloads for matching titles.
    logger:            Log messages to a logging.Logger instance.
    logtostderr:       Log messages to stderr instead of stdout.
    writedescription:  Write the video description to a .description file
    writeinfojson:     Write the video description to a .info.json file
    writeannotations:  Write the video annotations to a .annotations.xml file
    writethumbnail:    Write the thumbnail image to a file
    write_all_thumbnails:  Write all thumbnail formats to files
    writesubtitles:    Write the video subtitles to a file
    writeautomaticsub: Write the automatically generated subtitles to a file
    allsubtitles:      Downloads all the subtitles of the video
                       (requires writesubtitles or writeautomaticsub)
    listsubtitles:     Lists all available subtitles for the video
    subtitlesformat:   The format code for subtitles
    subtitleslangs:    List of languages of the subtitles to download
    keepvideo:         Keep the video file after post-processing
    daterange:         A DateRange object, download only if the upload_date is in the range.
    skip_download:     Skip the actual download of the video file
    cachedir:          Location of the cache files in the filesystem.
                       False to disable filesystem cache.
    noplaylist:        Download single video instead of a playlist if in doubt.
    age_limit:         An integer representing the user's age in years.
                       Unsuitable videos for the given age are skipped.
    min_views:         An integer representing the minimum view count the video
                       must have in order to not be skipped.
                       Videos without view count information are always
                       downloaded. None for no limit.
    max_views:         An integer representing the maximum view count.
                       Videos that are more popular than that are not
                       downloaded.
                       Videos without view count information are always
                       downloaded. None for no limit.
    download_archive:  File name of a file where all downloads are recorded.
                       Videos already present in the file are not downloaded
                       again.
    cookiefile:        File name where cookies should be read from and dumped to.
    nocheckcertificate:Do not verify SSL certificates
    prefer_insecure:   Use HTTP instead of HTTPS to retrieve information.
                       At the moment, this is only supported by YouTube.
    proxy:             URL of the proxy server to use
    geo_verification_proxy:  URL of the proxy to use for IP address verification
                       on geo-restricted sites. (Experimental)
    socket_timeout:    Time to wait for unresponsive hosts, in seconds
    bidi_workaround:   Work around buggy terminals without bidirectional text
                       support, using fridibi
    debug_printtraffic:Print out sent and received HTTP traffic
    include_ads:       Download ads as well
    default_search:    Prepend this string if an input url is not valid.
                       'auto' for elaborate guessing
    encoding:          Use this encoding instead of the system-specified.
    extract_flat:      Do not resolve URLs, return the immediate result.
                       Pass in 'in_playlist' to only show this behavior for
                       playlist items.
    postprocessors:    A list of dictionaries, each with an entry
                       * key:  The name of the postprocessor. See
                               youtube_dl/postprocessor/__init__.py for a list.
                       as well as any further keyword arguments for the
                       postprocessor.
    progress_hooks:    A list of functions that get called on download
                       progress, with a dictionary with the entries
                       * status: One of "downloading", "error", or "finished".
                                 Check this first and ignore unknown values.
                       If status is one of "downloading", or "finished", the
                       following properties may also be present:
                       * filename: The final filename (always present)
                       * tmpfilename: The filename we're currently writing to
                       * downloaded_bytes: Bytes on disk
                       * total_bytes: Size of the whole file, None if unknown
                       * total_bytes_estimate: Guess of the eventual file size,
                                               None if unavailable.
                       * elapsed: The number of seconds since download started.
                       * eta: The estimated time in seconds, None if unknown
                       * speed: The download speed in bytes/second, None if
                                unknown
                       * fragment_index: The counter of the currently
                                         downloaded video fragment.
                       * fragment_count: The number of fragments (= individual
                                         files that will be merged)
                       Progress hooks are guaranteed to be called at least once
                       (with status "finished") if the download is successful.
    merge_output_format: Extension to use when merging formats.
    fixup:             Automatically correct known faults of the file.
                       One of:
                       - "never": do nothing
                       - "warn": only emit a warning
                       - "detect_or_warn": check whether we can do anything
                                           about it, warn otherwise (default)
    source_address:    (Experimental) Client-side IP address to bind to.
    call_home:         Boolean, true iff we are allowed to contact the
                       youtube-dl servers for debugging.
    sleep_interval:    Number of seconds to sleep before each download when
                       used alone or a lower bound of a range for randomized
                       sleep before each download (minimum possible number
                       of seconds to sleep) when used along with
                       max_sleep_interval.
    max_sleep_interval:Upper bound of a range for randomized sleep before each
                       download (maximum possible number of seconds to sleep).
                       Must only be used along with sleep_interval.
                       Actual sleep time will be a random float from range
                       [sleep_interval; max_sleep_interval].
    listformats:       Print an overview of available video formats and exit.
    list_thumbnails:   Print a table of all thumbnails and exit.
    match_filter:      A function that gets called with the info_dict of
                       every video.
                       If it returns a message, the video is ignored.
                       If it returns None, the video is downloaded.
                       match_filter_func in utils.py is one example for this.
    no_color:          Do not emit color codes in output.
    geo_bypass:        Bypass geographic restriction via faking X-Forwarded-For
                       HTTP header (experimental)
    geo_bypass_country:
                       Two-letter ISO 3166-2 country code that will be used for
                       explicit geographic restriction bypassing via faking
                       X-Forwarded-For HTTP header (experimental)
    The following options determine which downloader is picked:
    external_downloader: Executable of the external downloader to call.
                       None or unset for standard (built-in) downloader.
    hls_prefer_native: Use the native HLS downloader instead of ffmpeg/avconv
                       if True, otherwise use ffmpeg/avconv if False, otherwise
                       use downloader suggested by extractor if None.
    The following parameters are not used by YoutubeDL itself, they are used by
    the downloader (see youtube_dl/downloader/common.py):
    nopart, updatetime, buffersize, ratelimit, min_filesize, max_filesize, test,
    noresizebuffer, retries, continuedl, noprogress, consoletitle,
    xattr_set_filesize, external_downloader_args, hls_use_mpegts.
    The following options are used by the post processors:
    prefer_ffmpeg:     If True, use ffmpeg instead of avconv if both are available,
                       otherwise prefer avconv.
    postprocessor_args: A list of additional command-line arguments for the
                        postprocessor.
    The following options are used by the Youtube extractor:
    youtube_include_dash_manifest: If True (default), DASH manifests and related
                        data will be downloaded and processed by extractor.
                        You can reduce network I/O by disabling it if you don't
                        care about DASH.
    """
