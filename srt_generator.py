def create_srt_file(subtitles, output_file):
    with open(output_file, 'w') as f:
        for index, (start_time, end_time, text) in enumerate(subtitles, start=1):
            f.write(str(index) + '\n')
            f.write("{:02d}:{:02d}:{:02d},{:03d} --> {:02d}:{:02d}:{:02d},{:03d}\n".format(
                int(start_time / 3600),
                int((start_time % 3600) / 60),
                int(start_time % 60),
                int((start_time % 1) * 1000),
                int(end_time / 3600),
                int((end_time % 3600) / 60),
                int(end_time % 60),
                int((end_time % 1) * 1000)
            ))
            f.write(text + '\n\n')

# Example usage:
# subtitles = [
#     (0, 5, "Hello, this is the first subtitle."),
#     (6, 10, "And here is the second subtitle."),
#     # Add more subtitles as needed
# ]

# create_srt_file(subtitles, "output.srt")
