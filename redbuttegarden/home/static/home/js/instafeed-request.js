const posts = [];

function assemblePosts() {
    const container = document.getElementById("images-container");

    posts.sort(function(x, y) {
        return new Date(y['timestamp']) - new Date(x['timestamp']);
    });

    for (const post of posts) {
        console.log('Assembling post...');

        let mediaParent = document.createElement('div');
        mediaParent.id = "media-parent";
        mediaParent.style = "margin-bottom: 3rem;";

        let mediaLink = document.createElement('a');
        mediaLink.href = post['permalink'];
        mediaLink.id = "media-link";
        mediaLink.style = "text-decoration: none;";

        let mediaImg = document.createElement('img');
        mediaImg.id = "media-img";

        mediaImg.src = post['media_url'];

        mediaImg.style = (window.matchMedia("(max-width: 420px) and (max-height: 830px)").matches
            ? "width: 150px; height: 150px;"
            : "width: 350px; height: 350px;");

        let mediaCaption = document.createElement('p');
        mediaCaption.id = "media-caption";
        mediaCaption.innerHTML = "(" + post['timestamp'].split("T")[0] + ")&nbsp;" + post['caption'];
        mediaCaption.style = "color: black; margin-top: 1rem;";

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
