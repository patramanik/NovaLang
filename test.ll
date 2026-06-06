; ModuleID = 'novalang'
source_filename = "main.nova"

declare i32 @printf(ptr, ...)
@str_format_int = private unnamed_addr constant [4 x i8] c"%d\0A\00", align 1
@str_format_float = private unnamed_addr constant [9 x i8] c"%.6f\0A\00", align 1
@str_format_string = private unnamed_addr constant [4 x i8] c"%s\0A\00", align 1
@str_format_bool_true = private unnamed_addr constant [6 x i8] c"true\0A\00", align 1
@str_format_bool_false = private unnamed_addr constant [7 x i8] c"false\0A\00", align 1
@x = global i32 0, align 4
@multiplier = global i32 0, align 4
@result = global i32 0, align 4

define i32 @multiply(i32 %val_param) {
entry:
    %val_slot = alloca i32, align 4
    store i32 %val_param, ptr %val_slot, align 4
    %reg_1 = load i32, ptr %val_slot, align 4
    %reg_2 = load i32, ptr @multiplier, align 4
    %reg_3 = mul i32 %reg_1, %reg_2
    ret i32 %reg_3
}

define i32 @main() {
entry:
    store i32 5, ptr @x, align 4
    store i32 10, ptr @multiplier, align 4
    %reg_4 = load i32, ptr @x, align 4
    %reg_5 = call i32 @multiply(i32 %reg_4)
    store i32 %reg_5, ptr @result, align 4
    %reg_6 = load i32, ptr @result, align 4
    call i32 (ptr, ...) @printf(ptr @str_format_int, i32 %reg_6)
    ret i32 0
}