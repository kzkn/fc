var selectedBldCds = [];
var selectedDays = [];
var canceled = false;

$(function() {
    var console_div = $('<div></div>', { id: 'console' }).insertBefore(court_table);
    $('#bldCdsAll').on('change', function() {
        $('input[name=bldCds]').prop('checked', $(this).prop('checked'));
    })
    $('#displayAvailable2').on('change', changeDisplayTarget);
    $('#displayAvailable').on('change', changeDisplayTarget);
    $('#displayReserved').on('change', changeDisplayTarget);
    $('input[name=bldCds]').on('change', function() {
        var bldCd = $(this).val();
        $('div[name=place' + bldCd + ']').toggle($(this).prop('checked'));
    });
});

function log(text) {
    $('<div></div>').append(text).appendTo($('#console'));
}

function changeDisplayTarget() {
    $('.hasAvailable2').toggle($('#displayAvailable2').prop('checked'));
    $('.hasAvailable').toggle($('#displayAvailable').prop('checked'));
    $('.allReserved').toggle($('#displayReserved').prop('checked'));
}

function search_court(url, bi, jsessionid) {
    if (bi == 0) {
        ready();
        selectedBldCds = [];
        $('input[name=bldCds]').each(function() {
            if ($(this).prop('checked'))
                selectedBldCds.push($(this).val());
        });
        selectedDays = [];
        $('input[name=days]').each(function() {
            selectedDays.push($(this).prop('checked') ? '1' : '0');
        });
    }
    if (bi >= selectedBldCds.length) {
        done(true);
        return;
    }
    if (canceled) {
        done(false);
        return;
    }
    progress(bi);
    var bldCd = selectedBldCds[bi];
    var data = { jsessionid: jsessionid, bldCd: bldCd, days: selectedDays };
    //log(bi + ', ' + bldCd + ': ' + JSON.stringify(data));
    $.ajax({
        type: 'POST',
        url: url,
        contentType: 'application/json; charset=utf-8',
        dataType: 'json',
        cache: false,
        data: JSON.stringify(data),
        //beforeSend: function(xhr) {
        //    xhr.overrideMimeType("text/html; charset=Shift_JIS");
        //},
    })
    .done(function(data, textStatus) {
        var bldCd = data['bldCd'];
        var place = data['place'];
        var dates = data['dates'];
        var jsessionid = data['jsessionid'];
        //console.log('place: ' + bldCd + ', ' + place);
        var table = $('#court_table');
        var date_panel_group = $('<div></div>', { 'class': 'panel-group' }).appendTo(table);
        for (var di in dates) {
            var date = dates[di];
            date_id = date.date.replace(/^(\d+)\/(\d+).*$/, '$1$2');
            //console.log('  date: ' + date.date + ', id: ' + date_id);
            var date_div = undefined;
            if (bldCd == selectedBldCds[0]) {
                var date_panel = $('<div></div>', { 'class': 'panel panel-default date' }).appendTo(date_panel_group);
                var date_panel_head = $('<div></div>', { 'class': 'panel-heading' }).appendTo(date_panel);

                $('<a></a>', { href: '#' + date_id + 'panel', 'data-toggle': "collapse" }).append(date.date).appendTo(date_panel_head);

                var date_panel_collapse = $('<div></div>', { id: date_id + 'panel', 'class': 'panel-collapse collapse' }).appendTo(date_panel);
                date_div = $('<div></div>', { id: date_id, 'class': 'panel-body' }).appendTo(date_panel_collapse);
            }
            else
                date_div = $('#' + date_id);
            var place_elm = $('<div name="place' + bldCd + '"></div>', { 'class': 'place' });
            date_div.append(place_elm);
            var place_name_elm = $('<h6></h6>', { 'class': 'place-name', text: place });
            place_elm.append(place_name_elm);
            var courts_elm = $('<div></div>', { 'class': 'courts' });
            place_elm.append(courts_elm);
            for (var ci in date.courts) {
                var court = date.courts[ci];
                var court_name = court.name;
                court_name = court_name.replace(/^テニス（(屋外|屋内)([０-９]+)）$/, "$1#$2");  // ex: 屋外#1
                court_name = court_name.replace(/^テニス(バレー)?コート([０-９]+).*$/, "#$2");  // ex: #1
                court_name = court_name.replace(/[Ａ-Ｚａ-ｚ０-９]/g, function(s) { return String.fromCharCode(s.charCodeAt(0)-0xFEE0) });
                //console.log('    court: ' + court_name);
                var court_elm = $('<div></div>', { 'class': 'court' });
                place_elm.append(court_elm);
                var court_name_elm = $('<div></div>', { 'class': 'court-name', text: court_name });
                court_elm.append(court_name_elm);
                var term_elm = $('<div></div>', { 'class': 'term' });
                court_elm.append(term_elm);
                var max_term = 0;
                for (var si in court.states) {
                    var state = court.states[si];
                    var term_regex = /^([0-9]+):[0-9]+-([0-9]+):[0-9]+$/;
                    var beg = state.term.replace(term_regex, "$1") - 0;
                    var end = state.term.replace(term_regex, "$2") - 0;
                    for (var i = beg; i < end; ++i) {
                        var klass;
                        var term = end - beg;
                        if (!state.reservable)
                            klass = 'reserved';
                        else {
                            if (term > max_term)
                                max_term = term;
                            klass = toHourClass(term);
                        }
                        var hour_elm = $('<div></div>', { 'class': 'hour', text: i }).addClass(klass);
                        term_elm.append(hour_elm);
                    }
                    //console.log('      ' + beg + '-' + end + ': ' + klass);
                }
                var klass = toCourtClass(max_term);
                court_elm.addClass(klass);
            }
        }
        $('input[name=bldCds][value="' + selectedBldCds[bi] + '"]').parent().removeClass('text-muted').addClass('text-primary');
        // TODO: 要素を追加する前に toggle させておきたい
        changeDisplayTarget();
        search_court(url, bi + 1, jsessionid)
    })
    .fail(function(data, textStatus, errorThrown) {
        $('<div></div>').append('Error! ' + textStatus + ' ' + errorThrown).appendTo($('#status'));
        done();
    });
}

function toHourClass(term) {
    switch (term) {
    case 0: return 'reserved';
//    case 1: return 'bg-warning';
//    case 2: return 'bg-info';
//    default: return 'bg-success';
    case 1: return 'available';
    case 2: return 'available2';
    default: return 'available3';
    }
}

function toCourtClass(term) {
    switch (term) {
    case 0: return 'allReserved';
    case 1: return 'hasAvailable';
    case 2: return 'hasAvailable2';
    default: return 'hasAvailable3';
    }
}

function cancel() {
    canceled = true;
    $('#cancel_button').addClass('disabled');
    $('#progressbar').addClass('progress-bar-danger');
    var status = $('#status');
    status.text('キャンセルしています...');
    status.removeClass('alert-info');
    status.addClass('alert-danger');
    //log('cancel!');
}

function ready() {
    canceled = false;
    $('#search_button').hide();
    $('#cancel_button').removeClass('disabled');
    $('#cancel_button').show();
    $('#console').empty();
    $('#court_table').empty();

    $('label[name=placeLabel]').removeClass('text-primary').addClass('text-muted');

    var status = $('#status');
    status.empty();
    status.removeClass('alert-danger');
    status.addClass('alert-info');
    var progressbar = $('#progressbar');
    progressbar.attr('aria-valuenow', 0);
    progressbar.css('width', '0%');
    $('#progressbar_sr').text('0%');
    progressbar.removeClass('progress-bar-danger');
    $('#progress').addClass('progress-striped active');
    var status_panel = $('#status_panel');
    status_panel.finish();
    status_panel.show();
}

function progress(bi) {
    var progressbar = $('#progressbar');
    var now = Math.round((bi + 1) * 100 / (selectedBldCds.length + 1));
    progressbar.attr('aria-valuenow', now);
    progressbar.css('width', now + '%');
    $('#progressbar_sr').text(now + '%');
    var place = $('input[name=bldCds][value="' + selectedBldCds[bi] + '"]').parent().text();
    $('#status').text('検索中... ' + place);
}

function done(isComplete) {
    $('#status').text(isComplete ? '完了!' : 'キャンセルしました。');
    if (isComplete) {
        var progressbar = $('#progressbar');
        progressbar.attr('aria-valuenow', 100);
        progressbar.css('width', '100%');
        $('#progressbar_sr').text('100%');
    }
    $('#progress').removeClass('progress-striped active');
    $('#status_panel').delay(2000).hide(0);
    $('#cancel_button').hide();
    $('#search_button').show();
}
