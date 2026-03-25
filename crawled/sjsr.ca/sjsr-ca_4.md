---
url: https://sjsr.ca/wp-content/cache/min/1/wp-content/plugins/wp-media-folder/assets/js/single_image_lightbox/single_image_lightbox.js?ver=1774398882
title: sjsr.ca
date_crawled: '2026-03-25T01:40:45Z'
source_domain: sjsr.ca
depth: 1
parent_url: https://sjsr.ca/
word_count: 11
rendering_mode: static
---

(function($){$(document).ready(function(){if(jQuery().magnificPopup){if($('.wpmf_image_lightbox, .open-lightbox-feature-image').length){$('.wpmf_image_lightbox, .open-lightbox-feature-image').magnificPopup({gallery:{enabled:!0,tCounter:'%curr% / %total%',arrowMarkup:''},callbacks:{elementParse:function(q){if(q.el.closest('a').length){q.src=q.el.closest('a').attr('href')}else{q.src=q.el.attr('src')}}},type:'image',showCloseBtn:!1,image:{titleSrc:'title'}})}
$('body a').each(function(i,v){if($(v).find('img[data-wpmflightbox="1"]').length!==0){$(v).magnificPopup({delegate:'img',gallery:{enabled:!0,tCounter:'%curr% / %total%',arrowMarkup:''},callbacks:{elementParse:function(q){var wpmf_lightbox=q.el.data('wpmf_image_lightbox');if(typeof wpmf_lightbox==="undefined"){q.src=q.el.attr('src')}else{q.src=wpmf_lightbox}}},type:'image',showCloseBtn:!1,image:{titleSrc:'title'}})}})}})})(jQuery)
