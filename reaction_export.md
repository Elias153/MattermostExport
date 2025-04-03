## Reaction Export

For reaction export this query (instead of the one at export_data_postgres in channelexport.py) manages to export the reactions and its respective counts.

Only issue : if a message has multiple different reactions, then the same message will get exported the same amount as the amount of distinct reactions it has.

It is unclear at the moment how to handle this, as you also have to export WHO actually reacted for each distinct reaction. My first instinct would be to create a separate csv export for this..

```sql
    SELECT
        Posts.CreateAt/1000 AS timestamp,
        UserName,
        Message,
        Posts.type,
        reactions.emojiname,
        CASE
          WHEN COUNT(*) = 1 THEN NULL
          ELSE COUNT(*)
        END AS reactions_count,
        CASE
            WHEN length(Posts.fileids) <= 2 THEN NULL
        ELSE Posts.fileids
        END AS fileids,
        fileinfo.name
    FROM
        Posts
        INNER JOIN Users ON Posts.UserId = Users.Id
        LEFT JOIN fileinfo ON Posts.id = fileinfo.postid
        LEFT JOIN reactions ON Posts.ChannelId = reactions.ChannelId AND Posts.id = reactions.postid
    WHERE
        Posts.editat = 0
        AND Posts.ChannelId = %s
        AND to_timestamp(Posts.CreateAt/1000) >= %s 
        AND editat = 0 AND to_timestamp(Posts.CreateAt/1000) < %s + interval '1 day' 
    group by reactions.emojiname, Posts.CreateAt, username, Posts.type, Posts.message, Posts.fileids, fileinfo.name
    ORDER BY Posts.CreateAt
```