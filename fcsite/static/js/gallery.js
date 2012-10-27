var onGetAlbum = function(response) {
    console.log(response);
    if (response.feed && response.feed.entry) {
        var albums = response.feed.entry;
        for (var i = 0, len = albums.length; i < len; ++i) {
            console.log('title: ' + albums[i].
        }
    }
}

var onGetPhoto = function(response) {
    $('#gallery .body').html('<img src="' + response.feed.entry[0].content.src + '">');
}

$(function() {
    function insertScript(query) {
        var script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = query;
        document.body.appendChild(script);
    }

    function showAlbumList() {
      insertScript('https://picasaweb.google.com/data/feed/api/user/113613698969275302586/?kind=album&alt=json-in-script&callback=onGetAlbum&max-results=1');
      //insertScript('https://picasaweb.google.com/data/feed/api/user/113613698969275302586/albumid/5102862630735366945?alt=json-in-script&callback=onGetAlbum&max-results=1');
    }

    showAlbumList();
});
