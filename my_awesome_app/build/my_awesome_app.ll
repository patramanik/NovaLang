; ModuleID = 'novalang'
source_filename = "main.nova"

declare i32 @printf(ptr, ...)
@str_format_int = private unnamed_addr constant [4 x i8] c"%d\0A\00", align 1
@str_format_float = private unnamed_addr constant [6 x i8] c"%.6f\0A\00", align 1
@str_format_string = private unnamed_addr constant [4 x i8] c"%s\0A\00", align 1
@str_format_bool_true = private unnamed_addr constant [6 x i8] c"true\0A\00", align 1
@str_format_bool_false = private unnamed_addr constant [7 x i8] c"false\0A\00", align 1
@welcomeMessage = global ptr null, align 4
@count = global i32 0, align 4
@inputVal = global i32 0, align 4
@squareResult = global i32 0, align 4
@.str.0 = private unnamed_addr constant [21 x i8] c"Hello from NovaLang!\00", align 1
@.str.1 = private unnamed_addr constant [26 x i8] c"Square is greater than 20\00", align 1
@.str.2 = private unnamed_addr constant [35 x i8] c"Square is less than or equal to 20\00", align 1
@.str.3 = private unnamed_addr constant [26 x i8] c"Pattern matching example:\00", align 1
@.str.4 = private unnamed_addr constant [4 x i8] c"One\00", align 1
@.str.5 = private unnamed_addr constant [20 x i8] c"Five - Match found!\00", align 1
@.str.6 = private unnamed_addr constant [12 x i8] c"Other value\00", align 1
@.str.7 = private unnamed_addr constant [36 x i8] c"Starter project execution complete!\00", align 1

define i32 @calculateSquare(i32 %n_param) {
entry:
    %n_slot = alloca i32, align 4
    store i32 %n_param, ptr %n_slot, align 4
    %reg_1 = load i32, ptr %n_slot, align 4
    %reg_2 = load i32, ptr %n_slot, align 4
    %reg_3 = mul i32 %reg_1, %reg_2
    ret i32 %reg_3
}

define i32 @main() {
entry:
    %reg_4 = getelementptr inbounds [21 x i8], ptr @.str.0, i64 0, i64 0
    store ptr %reg_4, ptr @welcomeMessage, align 4
    %reg_5 = load ptr, ptr @welcomeMessage, align 4
    call i32 (ptr, ...) @printf(ptr @str_format_string, ptr %reg_5)
    store i32 10, ptr @count, align 4
    store i32 5, ptr @inputVal, align 4
    %reg_6 = load i32, ptr @inputVal, align 4
    %reg_7 = call i32 @calculateSquare(i32 %reg_6)
    store i32 %reg_7, ptr @squareResult, align 4
    %reg_8 = load i32, ptr @squareResult, align 4
    %reg_9 = icmp sgt i32 %reg_8, 20
    br i1 %reg_9, label %if_then_1, label %if_else_2
if_then_1:
    %reg_10 = getelementptr inbounds [26 x i8], ptr @.str.1, i64 0, i64 0
    call i32 (ptr, ...) @printf(ptr @str_format_string, ptr %reg_10)
    br label %if_end_3
if_else_2:
    %reg_11 = getelementptr inbounds [35 x i8], ptr @.str.2, i64 0, i64 0
    call i32 (ptr, ...) @printf(ptr @str_format_string, ptr %reg_11)
    br label %if_end_3
if_end_3:
    %reg_12 = getelementptr inbounds [26 x i8], ptr @.str.3, i64 0, i64 0
    call i32 (ptr, ...) @printf(ptr @str_format_string, ptr %reg_12)
    %reg_13 = load i32, ptr @inputVal, align 4
    %reg_14 = icmp eq i32 %reg_13, 1
    br i1 %reg_14, label %match_case_0_5, label %match_next_0_6
match_case_0_5:
    %reg_15 = getelementptr inbounds [4 x i8], ptr @.str.4, i64 0, i64 0
    call i32 (ptr, ...) @printf(ptr @str_format_string, ptr %reg_15)
    br label %match_end_4
match_next_0_6:
    %reg_16 = icmp eq i32 %reg_13, 5
    br i1 %reg_16, label %match_case_1_7, label %match_next_1_8
match_case_1_7:
    %reg_17 = getelementptr inbounds [20 x i8], ptr @.str.5, i64 0, i64 0
    call i32 (ptr, ...) @printf(ptr @str_format_string, ptr %reg_17)
    br label %match_end_4
match_next_1_8:
    %reg_18 = getelementptr inbounds [12 x i8], ptr @.str.6, i64 0, i64 0
    call i32 (ptr, ...) @printf(ptr @str_format_string, ptr %reg_18)
    br label %match_end_4
match_end_4:
    %reg_19 = getelementptr inbounds [36 x i8], ptr @.str.7, i64 0, i64 0
    call i32 (ptr, ...) @printf(ptr @str_format_string, ptr %reg_19)
    ret i32 0
}