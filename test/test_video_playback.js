// 测试视频播放逻辑
// 模拟前端 JavaScript 的 playVideo 函数行为

function testPlayVideo() {
    console.log("=== 测试视频播放逻辑 ===\n");

    // 模拟视频元素
    let videoEl = {
        src: null,
        loop: false,
        onloadeddata: null,
        onended: null,
        onerror: null,
        style: { display: 'none' },
        play: function() {
            console.log("  🎬 video.play() 被调用");
            return Promise.resolve();
        }
    };

    // 模拟 playVideo 函数
    function playVideo(url, loop) {
        console.log(`\n📹 playVideo 被调用: url=${url}, loop=${loop}`);

        return new Promise((resolve, reject) => {
            videoEl.src = url;
            videoEl.loop = loop;

            // 清除之前的事件监听器
            console.log("  🧹 清除之前的事件监听器");
            videoEl.onloadeddata = null;
            videoEl.onended = null;
            videoEl.onerror = null;

            videoEl.onloadeddata = function() {
                console.log("  ✅ onloadeddata 触发");
                videoEl.style.display = "block";
                videoEl.play()
                    .then(() => {
                        console.log("  🎬 视频开始播放");
                        // 循环视频立即 resolve
                        if (loop) {
                            console.log("  🔄 循环视频，立即 resolve");
                            resolve();
                        }
                    })
                    .catch(e => {
                        console.error("  ❌ 视频播放失败:", e);
                        reject(e);
                    });
            };

            if (!loop) {
                videoEl.onended = function() {
                    console.log("  ✅ onended 触发");
                    resolve();
                };
            }

            videoEl.onerror = function(e) {
                console.error("  ❌ onerror 触发:", e);
                reject(e);
            };

            // 模拟视频加载完成
            console.log("  ⏳ 模拟视频加载...");
            setTimeout(() => {
                if (videoEl.onloadeddata) {
                    videoEl.onloadeddata();
                }
            }, 100);

            // 如果不是循环视频，模拟播放结束
            if (!loop) {
                setTimeout(() => {
                    if (videoEl.onended) {
                        videoEl.onended();
                    }
                }, 500);
            }
        });
    }

    // 测试场景：播放过渡视频，然后播放目标视频
    async function testTransitionFlow() {
        console.log("\n🎬 测试场景：过渡视频 -> 目标视频\n");

        try {
            console.log("1️⃣ 播放过渡视频 (loop=false)");
            await playVideo("/transition/working/speaking", false);
            console.log("   ✅ 过渡视频完成\n");

            console.log("2️⃣ 播放目标视频 (loop=true)");
            await playVideo("/video/speaking", true);
            console.log("   ✅ 目标视频完成\n");

            console.log("✅ 整个流程完成，应该通知服务器任务完成");

        } catch (error) {
            console.error("❌ 测试失败:", error);
        }
    }

    testTransitionFlow();
}

testPlayVideo();
