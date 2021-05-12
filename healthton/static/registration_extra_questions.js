traineeChecked = document.getElementById("user_type-0");
traineeChecked.addEventListener("click", hideTrainerExtraQuestion);
traineeChecked.addEventListener("click", hideGymManagerExtraQuestion);
//traineeChecked.addEventListener("click", hideOperatorExtraQuestion);

trainerChecked = document.getElementById("user_type-1");
trainerChecked.addEventListener("click", viewTrainerExtraQuestion);
trainerChecked.addEventListener("click", hideGymManagerExtraQuestion);
//trainerChecked.addEventListener("click", hideOperatorExtraQuestion);

gymManagerChecked = document.getElementById("user_type-2");
gymManagerChecked.addEventListener("click", hideTrainerExtraQuestion);
gymManagerChecked.addEventListener("click", viewGymManagerExtraQuestion);
//gymManagerChecked.addEventListener("click", hideOperatorExtraQuestion);

//operatorChecked = document.getElementById("user_type-3");
//operatorChecked.addEventListener("click", hideTrainerExtraQuestion);
//operatorChecked.addEventListener("click", hideGymManagerExtraQuestion);
//operatorChecked.addEventListener("click", viewOperatorExtraQuestion);

function viewTrainerExtraQuestion() {
    trainerExtraQuestion = document.getElementById("trainer_extra_question");
    trainerExtraQuestion.style.display = "block";
}

function hideTrainerExtraQuestion() {
    trainerExtraQuestion = document.getElementById("trainer_extra_question");
    trainerExtraQuestion.style.display = "none";
}

function viewGymManagerExtraQuestion() {
    gymManagerExtraQuestion = document.getElementById("gym_manager_extra_question");
    gymManagerExtraQuestion.style.display = "block";
}

function hideGymManagerExtraQuestion() {
    gymManagerExtraQuestion = document.getElementById("gym_manager_extra_question");
    gymManagerExtraQuestion.style.display = "none";
}

//function viewOperatorExtraQuestion() {
//    operatorExtraQuestion = document.getElementById("operator_extra_question");
//    operatorExtraQuestion.style.display = "block";
//}
//
//function hideOperatorExtraQuestion() {
//    operatorExtraQuestion = document.getElementById("operator_extra_question");
//    operatorExtraQuestion.style.display = "none";
//}