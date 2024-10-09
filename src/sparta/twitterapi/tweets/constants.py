# Created from the Twitter OpenAPI Spec
# https://api.twitter.com/2/openapi.json
FIELD_SELECTORS = "tweet.fields=id,created_at,text,author_id,in_reply_to_user_id,referenced_tweets,attachments,withheld,geo,entities,public_metrics,possibly_sensitive,source,lang,context_annotations,conversation_id,reply_settings&expansions=attachments.poll_ids,attachments.media_keys,author_id,entities.mentions.username,geo.place_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id&user.fields=created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,withheld&media.fields=media_key,duration_ms,height,preview_image_url,type,url,width,public_metrics,alt_text,variants"  # noqa

TWEET_FIELDS = "article,attachments,author_id,card_uri,context_annotations,conversation_id,created_at,display_text_range,edit_controls,edit_history_tweet_ids,entities,geo,id,in_reply_to_user_id,lang,media_metadata,note_tweet,possibly_sensitive,public_metrics,referenced_tweets,reply_settings,scopes,source,text,withheld"  # noqa
EXPANSIONS = "article.cover_media,article.media_entities,attachments.media_keys,attachments.media_source_tweet,attachments.poll_ids,author_id,edit_history_tweet_ids,entities.mentions.username,geo.place_id,in_reply_to_user_id,entities.note.mentions.username,referenced_tweets.id,referenced_tweets.id.author_id"  # noqa
USER_FIELDS = "affiliation,connection_status,created_at,description,entities,id,location,most_recent_tweet_id,name,pinned_tweet_id,profile_banner_url,profile_image_url,protected,public_metrics,receives_your_dm,subscription_type,url,username,verified,verified_type,withheld"  # noqa
MEDIA_FIELDS = "media_key,duration_ms,height,preview_image_url,type,url,width,public_metrics,alt_text,variants"
POLL_FIELDS = "duration_minutes,end_datetime,id,options,voting_status"
PLACE_FIELDS = "contained_within,country,country_code,full_name,geo,id,name,place_type"
USER_EXPANSIONS = "affiliation.user_id,most_recent_tweet_id,pinned_tweet_id"
