#include <stdio.h>
#include <string.h>
#include <regex.h>

#define EMAIL_SIZE 100

int isValidEmail(const char *email)
{
   regex_t regex;

   const char *pattern =
       "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$";

   int result = regcomp(&regex, pattern, REG_EXTENDED);

   if (result != 0)
   {
       printf("정규표현식 컴파일 오류\n");
       return 0;
   }

   result = regexec(&regex, email, 0, NULL, 0);

   regfree(&regex);

   return result == 0;
}

void removeNewLine(char *str)
{
   str[strcspn(str, "\n")] = '\0';
}

int main()
{
   char email[EMAIL_SIZE];

   while (1)
   {
       printf("이메일 입력: ");
       fgets(email, sizeof(email), stdin);

       removeNewLine(email);

       if (isValidEmail(email))
       {
           printf("올바른 이메일 형식입니다: %s\n", email);
           break;
       }
       else
       {
           printf("잘못된 이메일 형식입니다. 다시 입력하세요.\n");
       }
   }

   return 0;
}
