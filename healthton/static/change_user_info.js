changeInfo = document.getElementById("change_info");
changeInfo.addEventListener("click", showMoreOption);

showMoreOption = function(){
    test = document.getElementById("test");
    test.style.color="red";
    ChangedInfo = document.getElementById("changed_info");
    ChangedInfo.style.display = "block";
}