section .data
    .str.fmt.2567893330 db "%d\n", 0

section .text
    extern printf
    source_filename = "<string>"
    target triple = "unknown-unknown-unknown"
    global _start

_start:
      ; Translated code will be inserted here
    entry:
    %.22 = tail call i32 (i8*, ...) @printf(i8* nonnull dereferenceable(1) getelementptr inbounds ([4 x i8], [4 x i8]* @.str.fmt.2567893330, i64 0, i64 0), i32 7)
    %.25 = tail call i32 (i8*, ...) @printf(i8* nonnull dereferenceable(1) getelementptr inbounds ([4 x i8], [4 x i8]* @.str.fmt.2567893330, i64 0, i64 0), i32 3)
    %.28 = tail call i32 (i8*, ...) @printf(i8* nonnull dereferenceable(1) getelementptr inbounds ([4 x i8], [4 x i8]* @.str.fmt.2567893330, i64 0, i64 0), i32 10)
    %.31 = tail call i32 (i8*, ...) @printf(i8* nonnull dereferenceable(1) getelementptr inbounds ([4 x i8], [4 x i8]* @.str.fmt.2567893330, i64 0, i64 0), i32 1)
    ret i32 0
    }
    attributes #0 = { nofree nounwind }
    mov rax, 60
    xor rdi, rdi
    syscall