sliderImages = [
   "/static/images/slider_pic1.jpg",
   "/static/images/slider_pic2.jpg",
   "/static/images/slider_pic3.jpg",
   "/static/images/slider_pic4.jpg"
];

sliderLeft = document.querySelector(".side_image_left");
sliderRight = document.querySelector(".side_image_right");

sliderLeft.src = sliderImages[sliderImages.length - 1];
sliderRight.src = sliderImages[2];

let observer = new MutationObserver(callback);

num = 1;
function callback () {
    if (num == 0) {
        sliderLeft.src = sliderImages[sliderImages.length - 1];
    } else {
        sliderLeft.src = sliderImages[num - 1];
    }

    if (num < sliderImages.length - 1) {
        sliderRight.src = sliderImages[num + 1];
        num++;
    }
    else {
        sliderRight.src = sliderImages[0];
        num = 0;
    }
}

CurrentSlide = document.querySelector("ul.carousel-indicators");
observer.observe(CurrentSlide, {
  attributes: true,
  attributeFilter: ['class'],
  childList:true,
  subtree:true}
);