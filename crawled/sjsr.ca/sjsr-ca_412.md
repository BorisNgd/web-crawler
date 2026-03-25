---
url: https://sjsr.ca/wp-content/plugins/wp-media-folder/assets/js/single_image_lightbox/single_image_lightbox.js?ver=6.1.11
title: sjsr.ca
date_crawled: '2026-03-25T01:47:43Z'
source_domain: sjsr.ca
depth: 2
parent_url: https://sjsr.ca/communiques/recherche-de-victimes-potentielles-de-miguel-theriault/
word_count: 144
rendering_mode: static
---

(function ($) {
$(document).ready(function () {
if (jQuery().magnificPopup) {
/* open lightbox when click to image */
if ($('.wpmf_image_lightbox, .open-lightbox-feature-image').length) {
$('.wpmf_image_lightbox, .open-lightbox-feature-image').magnificPopup({
gallery: {
enabled: true,
tCounter: '%curr% / %total%',
arrowMarkup: '' // markup of an arrow button
},
callbacks: {
elementParse: function (q) {
if (q.el.closest('a').length) {
q.src = q.el.closest('a').attr('href');
} else {
q.src = q.el.attr('src');
}
}
},
type: 'image',
showCloseBtn: false,
image: {
titleSrc: 'title'
}
});
}
/* open lightbox when click to image */
$('body a').each(function(i,v){
if($(v).find('img[data-wpmflightbox="1"]').length !== 0){
$(v).magnificPopup({
delegate: 'img',
gallery: {
enabled: true,
tCounter: '%curr% / %total%',
arrowMarkup: '' // markup of an arrow button
},
callbacks: {
elementParse: function(q) {
var wpmf_lightbox = q.el.data('wpmf_image_lightbox');
if(typeof wpmf_lightbox === "undefined"){
q.src = q.el.attr('src');
}else{
q.src = wpmf_lightbox;
}
}
},
type: 'image',
showCloseBtn : false,
image: {
titleSrc: 'title'
}
});
}
});
}
});
})(jQuery);
