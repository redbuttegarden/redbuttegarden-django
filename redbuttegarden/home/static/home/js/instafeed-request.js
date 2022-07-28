const posts = [];

function assemblePosts() {
    const container = document.getElementById("images-container");

    posts.sort(function(x, y) {
        return new Date(y['timestamp']) - new Date(x['timestamp']);
    });

    for (const post of posts) {
        let mediaParent = document.createElement('div');
        mediaParent.className = "media-parent";

        let mediaLink = document.createElement('a');
        mediaLink.href = post['permalink'];
        mediaLink.className = "media-link";

        let mediaImg = document.createElement('img');
        mediaImg.src = post['media_url'];
        mediaImg.className = "media-img";

        let mediaCaption = document.createElement('p');
        mediaCaption.innerHTML = "(" + post['timestamp'].split("T")[0] + ")&nbsp;" + post['caption'];
        mediaCaption.className = "media-caption";

        container.appendChild(mediaParent);
        mediaParent.appendChild(mediaLink);
        mediaLink.appendChild(mediaImg);
        mediaLink.appendChild(mediaCaption);
    }
}

async function fetchInstaIds(access_token) {
    return await fetch(`https://graph.instagram.com/me/media?fields=id&access_token=${access_token}`)
        .then(res => res.json())
        .then(json => {
            const ids = [];
            for (let obj of json["data"])
                ids.push(obj.id);

            return ids;
        })
}

function fetchInstaPosts(ids, access_token) {
    return Promise.all(ids.map((id) => {
        return fetch(`https://graph.instagram.com/${id}?fields=media_url,caption,permalink,media_type,timestamp&access_token=${access_token}`)
        .then(res => res.json())
        .then(post => {
            let media_url = (post.media_type === "IMAGE" ? post.media_url : "");
            let permalink = (post.media_type === "IMAGE" ? post.permalink : "");
            let caption = (post.media_type === "IMAGE" ? post.caption : "");
            let timestamp = (post.media_type === "IMAGE" ? post.timestamp : "");
            if (media_url != "") {
                let post_detail = {
                    'media_url': media_url,
                    'permalink': permalink,
                    'caption': caption,
                    'timestamp': timestamp
                };
                posts.push(post_detail);
            }
        });
    }));
}

async function fetchInsta() {
    const access_token = window.document.getElementById("fb_token").innerText;
    const ids = await fetchInstaIds(access_token);

    await fetchInstaPosts(ids, access_token);
    
    assemblePosts();
}
