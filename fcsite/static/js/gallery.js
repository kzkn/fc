var ALBUM_BASE_URL = null;  // ロードする側で設定する。
var USER_ID = '116368120089675858953';
var THUMBNAIL_SIZE = 160;

var appendThumbnailFor = function(thumbnails, makers) {
    return function(i, item) {
        var thumbnailUrl = item.media$group.media$thumbnail[0].url;
        var title = makers.titleMaker(item);
        var href = makers.urlMaker(item);

        /*
         * Build DOM:
         *
         * div class="row"
         *   div class="col-sm-6 col-md-3"
         *     a href="..." class="thumbnail"
         *      img src="..." title="..." alt="..."
         *      div class="caption"
         *        p
         */
        thumbnails
          .append($('<div/>').addClass('col-sm-6 col-md-3')
            .append($('<a/>').addClass('thumbnail').attr('href', href)
              .append($('<img/>').attr('src', thumbnailUrl)
                                 .attr('title', title)
                                 .attr('alt', title))
              .append($('<div/>').addClass('caption')
                .append($('<p/>').text(title)))));
    };
}

var onGetAlbum = function(response) {
    if (response.feed && response.feed.entry) {
        var thumbnails = $('<div/>').attr('class', 'row')
        $('#gallery').append(thumbnails);
        $.each(response.feed.entry, appendThumbnailFor(thumbnails, {
            urlMaker: function(item) { return ALBUM_BASE_URL.replace('1732847819758319743', item.gphoto$id.$t); },
            titleMaker: function(item) { return item.media$group.media$title.$t; }
        }));
    }
}

var onGetPhoto = function(response) {
    if (response.feed && response.feed.entry) {
        var thumbnails = $('<div/>').attr('class', 'row')
        $('#gallery')
          .append($('<h2/>').text(response.feed.title.$t + ' ')
            .append($('<small/>').text(response.feed.subtitle.$t)))
          .append(thumbnails);

        $.each(response.feed.entry, appendThumbnailFor(thumbnails, {
            urlMaker: function(item) { return item.content.src; },
            titleMaker: function(item) { return item.summary.$t; }
        }));
    }
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

var showPhotoList = function(albumId) {
    insertScript('http://picasaweb.google.com/data/feed/api/user/' + USER_ID + '/albumid/' + albumId +
                 '?kind=photo&access=visible&alt=json-in-script' +
                 '&thumbsize=' + THUMBNAIL_SIZE + 'c&callback=onGetPhoto');
}
