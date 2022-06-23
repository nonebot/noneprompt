from argparse import ArgumentParser

# question mark option
question_mark_option = ArgumentParser(add_help=False)
question_mark_option.add_argument(
    "-qm", "--question-mark", required=False, help="question mark"
)

# question mark style option
question_mark_style_option = ArgumentParser(add_help=False)
question_mark_style_option.add_argument(
    "-qms", "--question-mark-style", required=False, help="question mark style"
)

# question style option
question_style_option = ArgumentParser(add_help=False)
question_style_option.add_argument(
    "-qs", "--question-style", required=False, help="question style"
)

# annotation option
annotation_option = ArgumentParser(add_help=False)
annotation_option.add_argument(
    "-an", "--annotation", required=False, help="annotation texts"
)

# annotation style option
annotation_style_option = ArgumentParser(add_help=False)
annotation_style_option.add_argument(
    "-ans", "--annotation-style", required=False, help="annotation style"
)

# answer style option
answer_style_option = ArgumentParser(add_help=False)
answer_style_option.add_argument(
    "-as", "--answer-style", required=False, help="answer style"
)

# pointer option
pointer_option = ArgumentParser(add_help=False)
pointer_option.add_argument("-p", "--pointer", required=False, help="pointer mark")

# pointer style option
pointer_style_option = ArgumentParser(add_help=False)
pointer_style_option.add_argument(
    "-ps", "--pointer-style", required=False, help="pointer mark style"
)

# sign option
sign_option = ArgumentParser(add_help=False)
sign_option.add_argument("-s", "--sign", required=False, help="sign mark")

# sign style option
sign_style_option = ArgumentParser(add_help=False)
sign_style_option.add_argument(
    "-ss", "--sign-style", required=False, help="sign mark style"
)

# unsign option
unsign_option = ArgumentParser(add_help=False)
unsign_option.add_argument("-u", "--unsign", required=False, help="unsign mark")

# unsign style option
unsign_style_option = ArgumentParser(add_help=False)
unsign_style_option.add_argument(
    "-us", "--unsign-style", required=False, help="unsign mark style"
)

# select style option
select_style_option = ArgumentParser(add_help=False)
select_style_option.add_argument(
    "-ses", "--select-style", required=False, help="select mark style"
)

# unselect style option
unselect_style_option = ArgumentParser(add_help=False)
unselect_style_option.add_argument(
    "-unses", "--unselect-style", required=False, help="unselect mark style"
)

# filter style option
filter_style_option = ArgumentParser(add_help=False)
filter_style_option.add_argument("-f", "--filter", required=False, help="filter style")
