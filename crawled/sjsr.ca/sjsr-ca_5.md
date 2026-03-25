---
url: https://sjsr.ca/wp-content/cache/min/1/wp-content/plugins/ajax-searchwp/assets/js/script.js?ver=1774398882
title: sjsr.ca
date_crawled: '2026-03-25T01:41:29Z'
source_domain: sjsr.ca
depth: 1
parent_url: https://sjsr.ca/
word_count: 6
rendering_mode: static
---

jQuery(document).ready(function($){$('#s').on('keyup',function(){var query=$(this).val().trim();if(query.length>2){searchwp_ajax_search(query)}});$('#searchform').on('submit',function(e){if($('#s').val().trim()===''){e.preventDefault()}});$('#searchsubmit').on('click',function(e){if($('#s').val().trim()===''){e.preventDefault()}else{$('#searchform').submit()}});function searchwp_ajax_search(query){$.ajax({url:ajax_searchwp_object.ajax_url,type:'POST',data:{action:'ajax_searchwp_handle_search',query:query,nonce:ajax_searchwp_object.ajax_nonce},success:function(response){var resultsContainer=$('#ajax_searchwp_results');resultsContainer.empty();if(response.success&&response.data.length>0){response.data.forEach(function(result){resultsContainer.append('

')})}else{resultsContainer.append(''+ajax_searchwp_object.no_results_text+'

')}}})}})
