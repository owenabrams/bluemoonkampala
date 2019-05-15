 /*

 author: Tangqi Feng 

 function : calculate the BMI

 */


 function lookme(form) {
     var bmi;
     if (!checkform(form)) return false;
     comput(form);
     bmi = form.weight.value * 10000 / eval(form.height.value * form.height.value);
     form2.bmi.value = bmi;
     if (bmi > 40) {
         form2.nowstat.value = "Obese: Wow, just wow!. We need to talk. Urgently! We also need to see a doctor!";
     } else if (bmi > 30) {
         form2.nowstat.value = "Obese: Your health may be at risk if you do not lose weight. Book a session with mama fitness members for advise.";
     } else if (bmi > 25) {
         form2.nowstat.value = "Overweight: Weight loss plan? You are advised to lose some weight for health reasons. We recommended you to talk to mama fitness councilors!";
     } else if (bmi > 22) {
         form2.nowstat.value = "Healthy weight: Slightly fat, you can eat less. Also a lot of exercise - Simply follow our workout scheme based on your BMI ! :)";
     } else if (bmi >= 21) {
         form2.nowstat.value = "Healthy weight: I am so envious of your figure ! :) you are at a healthy weight for your height. By maintaining a healthy weight, you lower your risk of developing serious health problems.";
     } else if (bmi >= 18) {
         form2.nowstat.value = "Healthy weight: Slightly thin,You should eat more !";
     } else if (bmi >= 16) {
         form2.nowstat.value = "Underweight: Hurry to eat! You are recommended to ask a mama fitness instructor for advice. !";
     } else {
         form2.nowstat.value = "Underweight: Wow ! We need to see a doctor !! ";
     }
     return true;
 }

 function comput(form) {
     if (form.sex.options.selectedIndex == "0")
         form2.legendweight.value = Math.round(50 + (2.3 * (form.height.value - 152)) / 2.54);
     else
         form2.legendweight.value = Math.round(45.5 + (2.3 * (form.height.value - 152)) / 2.54);
 }

 function checkform(form) {
     if (form.weight.value == null || form.weight.value.length == 0 ||
         form.height.value == null || form.height.value.length == 0) {
         alert("Do you think I am God ? You do not tell me anything, how do I calculate !!!");
         return false;
     }
     if (form.weight.value <= 0) {
         alert("You will hit the lightest Guinness world record, be careful of gravity does not work for you !");
         return false;
     }
     if (form.weight.value > 500) {
         alert("You do not test, Your weight has crushed my scales.");
         return false;
     }
     if (form.height.value <= 0) {
         alert("You so short, smaller than the ants ?");
         return false;
     }
     if (form.height.value >= 300) {
         alert("you are so tall ! Can you help me pick the stars ?");
         return false;
     }
     return true;
 }

 function ClearForm() {
     form2.bmi.value = "";
     form2.nowstat.value = "";
     form2.legendweight.value = "";
 }