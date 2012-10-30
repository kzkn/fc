var ALBUM_BASE_URL = null;  // ロードする側で設定する
var USER_ID = '113613698969275302586';
var THUMBNAIL_SIZE = 160;

var appendThumbnailFor = function(thumbnails) {
    return function(i, item) {
        var title = item.media$group.media$title.$t;
        var thumbnailUrl = item.media$group.media$thumbnail[0].url;
        var albumId = item.gphoto$id.$t;
        var href = ALBUM_BASE_URL.replace('@albumid@', albumId);

        /*
         * Build DOM:
         *
         * ul class="thumbnails"
         *   li class="span2"
         *     div class="thumbnail"
         *       a href="..."
         *         img src="..." title="..." alt="..."
         *       p class="desc"
         */
        thumbnails
          .append($('<li/>').addClass('span2')
            .append($('<div/>').addClass('thumbnail')
              .append($('<a/>').attr('href', href)
                .append($('<img/>').attr('src', thumbnailUrl)
                                   .attr('title', title)
                                   .attr('alt', title)))
              .append($('<p/>').addClass('desc')
                               .text(title))));
    };
}

var onGetAlbum = function(response) {
    var thumbnails = $('<ul/>').attr('class', 'thumbnails')
    $('#gallery').append(thumbnails);

    if (response.feed && response.feed.entry)
        $.each(response.feed.entry, appendThumbnailFor(thumbnails));
}

var insertScript = function(query) {
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = query;
    document.body.appendChild(script);
}

var showAlbumList = function() {
    insertScript('http://picasaweb.google.com/data/feed/api/user/' + USER_ID +
                 '?kind=album&access=visible&alt=json-in-script' +
                 '&thumbsize=' + THUMBNAIL_SIZE + 'c&callback=onGetAlbum');
}
