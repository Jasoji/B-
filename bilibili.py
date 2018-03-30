# -*- coding: utf-8 -*-

import sys
import os
import re
import shutil
#imp.reload(sys)
#sys.setdefaultencoding("utf-8")
bili_path = "D:\\bilibili"


true = True
false = False
success = 0
fail = 0
merge = 0
problem_folder = []
#
#
#
class FlV :
    import binascii
    b2a = binascii.b2a_hex # hex 2 ascii-hex
    a2b = binascii.a2b_hex # ascii-hex 2 hex
    #
    #
    def IsFlv(self, obj):
        if type(obj) != type(b"abc") :
            obj = obj.read()
        if obj[0:3] == b"FLV" :
            return True
        else:
            return False
    #
    #
    def ProgressBar(self, now, total) :  # st =r"[################                                ]  12%"
        compiled = 66 * now // total
        print("\r[" + ">"*compiled + " "*(66 - compiled) + "]  %f%%"%((now * 100 / total)), end=" ")
    #
    #
    def MergeVideo(self, FileList, FilePath="", OutputPath="", DeleteThisPath=False) :
        global problem_folder, merge
        DealFileNumber = 0
        OutputFile = open(OutputPath + "out.mp4", "wb")
        TagDataLen = 0
        TagTimeStamp = 0
        LastTagTime = 0
        LastTagSize = False
        print("To:\t", OutputPath+"out.mp4")

        # 如果只有一个文件就直接复制出来吧，免得合并
        if len(FileList) == 1:
            self.ProgressBar(0, 1)
            OutputFile.close()
            shutil.copy(FilePath+FileList[0], OutputPath+"out.mp4")
            self.ProgressBar(1, 1)
            merge += 1
            if DeleteThisPath :
                try :
                    shutil.rmtree(FilePath)
                    print("已删除该文件夹\n")
                except WindowsError as e :
                    print("该路径有文件被占用，暂时无法删除\n")
            else :
                print("没有删除该文件夹\n")
            return None
        # 合并文件
        for EachFlv in FileList :
            self.ProgressBar(DealFileNumber, len(FileList))
            DealFileNumber += 1
            f = open(FilePath + EachFlv, "rb")
            VideoFile = f.read()
            f.close()
            if not self.IsFlv(VideoFile):
                print("这些视频里有些不是flv格式的\n")
                try:
                    if FilePath == "":
                        FilePath = os.getcwd()
                    problem_folder.append( (FilePath, "这些视频暂时不支持转换") )
                except:
                    pass
                finally:
                    OutputFile.close()
                    os.remove(OutputPath+"out.mp4")
                    return None

            if not LastTagSize :  # 第一个文件要写入flv的头
                OutputFile.write(VideoFile[:9])
            TagPosition = 9
            # 开始合并这个文件的tag
            while TagPosition + 5 < len(VideoFile) :
                # 记录这个Tag的时间戳和data长度
                TagTimeStamp = int(
                    self.b2a(
                        VideoFile[TagPosition+11 : TagPosition+12] +
                        VideoFile[TagPosition+8 : TagPosition+11]
                    ), 16
                )
                TagDataLen = int(
                    self.b2a(
                        VideoFile[TagPosition+5 :TagPosition+8]
                    ), 16
                )
                # 写入前一个tag的大小
                if not LastTagSize :
                    OutputFile.write(VideoFile[TagPosition : TagPosition+4])
                else :
                    OutputFile.write(LastTagSize)
                    LastTagSize = None
                # 写入这个tag的种类和data大小
                OutputFile.write(VideoFile[TagPosition+4 :TagPosition+8])
                # 写入这个tag的时间戳
                if not LastTagTime :
                    FullTimeStamp = hex(TagTimeStamp)[2:].zfill(8)
                    OutputFile.write(
                        self.a2b(
                            FullTimeStamp[2:] + FullTimeStamp[:2]
                        )
                    )
                else :
                    FullTimeStamp = hex(LastTagTime + TagTimeStamp)[2:].zfill(8)#去掉hex转换出来的0x，补全8个字节
                    OutputFile.write(
                        self.a2b(
                            FullTimeStamp[2:] + FullTimeStamp[:2]
                        )
                    )
                # 写入tag的data
                OutputFile.write(VideoFile[TagPosition + 12 :TagPosition + 15 + TagDataLen])
                # 更新为下一个tag的位置
                TagPosition += TagDataLen + 15
            else :
                # 为下一个文件作铺垫
                LastTagSize = TagDataLen + 15
                LastTagSize = self.a2b(
                    hex(LastTagSize)[2:].zfill(8)
                )
                LastTagTime += TagTimeStamp
        self.ProgressBar(DealFileNumber, len(FileList))
        OutputFile.close()
        merge += 1
        if DeleteThisPath:
            try:
                shutil.rmtree(FilePath)
                print("已删除该文件夹\n")
            except WindowsError as e:
                print("该路径有文件被占用，暂时无法删除\n")
        else:
            print("没有删除该文件夹\n")
#
#
#
def IsAddrInList(Str):
    for i in problem_folder:
        if Str in i[0]:
            return True
    else:
        return False
#
#
#
def RenameMp4(Addr, VideoFileName):
    global success, fail, problem_folder
    json_filename = "entry.json"
    try :
        f = open(Addr + os.sep + json_filename, encoding="utf-8")
        text = eval(f.read())
        f.close()
    except BaseException as e :
        fail += 1
        print(Addr)
        print("打开entry.json失败", e, end="\n")
        if not IsAddrInList(Addr) :
            problem_folder.append((Addr, "打开entry.json失败"))
        return None

    if "page_data" in list(text.keys()) :  # 普通文件
        title = str(text["title"])
        index = str(text["page_data"]["page"])
        index_title = str(text["page_data"]["part"])
    else :  # 番剧文件
        title = str(text["title"])
        index = str(text["ep"]["index"])
        index_title = str(text["ep"]["index_title"])
    change_name = title + " " + index + " " + index_title

    # 换掉文件名的非法字符
    for i in "/\:*?<>|\"" :
        if i in change_name :
            change_name = change_name.replace(i, "_")

    try :
        try:
            print(Addr + os.sep + "\n" + \
                  "Change: " + VideoFileName + "\n" + \
                  "To:     " + change_name.strip() + ".mp4")
        except UnicodeEncodeError: #一旦文件名夹杂了写奇怪的字符就报错，比如♪，处理方法居然和2.x不同，最下面写except也是这个原因
            print(Addr + os.sep + "\n" + \
                  "Change: " + VideoFileName + "\n" + \
                  "To:     " + change_name.encode("gbk", "ignore").decode("gbk").strip() + ".mp4")
        os.rename(Addr + os.sep + VideoFileName, change_name.strip() + ".mp4")
        print("成功", "\n")
        success += 1
    except WindowsError as e :
        print("无法重命名文件，也许当前目录已存在同名文件")
        try:
            print(e, "\n")
        except UnicodeEncodeError:
            print(str(e).encode("gbk", "ignore").decode("gbk"), "\n")
        if not IsAddrInList(Addr):
            problem_folder.append((Addr, change_name+"\n无法重命名文件，也许当前目录已存在同名文件"))
        fail += 1
#
#
#
def main():
    Flv = FlV()
    global fail, success, problem_folder
    # 合并视频
    for EachAddr in os.walk(bili_path, "r", "uft-8"):
        if EachAddr[1] == []:
            if "entry.json" in EachAddr[2]:
                continue
            # 视频的文件夹
            VideoPath = EachAddr[0]+os.sep
            # 父目录
            FatherPath = EachAddr[0][:EachAddr[0].rfind(os.sep)+1]
            # 在目录中找出视频文件名
            FilteredFile = str(EachAddr[2])
            FilteredFile = re.findall("\d+?\.mp4", FilteredFile) + re.findall("\d+?\.flv", FilteredFile) + re.findall("\d+?\.blv", FilteredFile)
            # 消除重复文件名
            MergeList = set()
            MergeList.update(FilteredFile)
            # 这样排序会有问题的["0.mp4", "1.mp4", "10.mp4", "11.mp4", "12.mp4", "13.mp4", "14.mp4", "15.mp4", "16.mp4", "17.mp4", "18.mp4", "19.mp4", "2.mp4", "3.mp4", "4.mp4", "5.mp4", "6.mp4", "7.mp4", "8.mp4", "9.mp4"]
            #MergeList = sorted(MergeList)  #按照文件名排列，以免合并顺序有问题
            MergeList = sorted(MergeList)
            if len(MergeList) > 10:
                ii = len(MergeList)
                ExtensionName = MergeList[0][-4:]
                MergeList = []
                for i in range(ii):
                    MergeList.append(str(i)+ExtensionName)
            # 如果那个文件夹里有视频文件就合并
            if MergeList != []:
                print(VideoPath)
                print("开始合并该文件夹的视频\t", MergeList)
                Flv.MergeVideo(MergeList, VideoPath, OutputPath=FatherPath, DeleteThisPath=True)

    # 开始重命名
    for EachAddr in os.walk(bili_path, "r", "utf-8"):
        # 返回内容("当前路径", [有什么文件夹], [有什么文件])
        if "entry.json" in EachAddr[2]:                                 #如果那个文件夹里有entry.json
            for EachFile in EachAddr[2]:
                if "mp4" in EachFile or "flv" in EachFile:          #如果该文件夹没有mp4或flv就跳过
                    video_filename = EachFile
                    addr = EachAddr[0]
                    # json_filename = "entry.json"
                    break
            else:
                continue
            # 改名
            RenameMp4(addr, video_filename)

    # 最后的总结
    print("\a")
    print("Merge:   ", merge)
    print("Success: ", success)
    print("Fail:    ", fail)
    print("Total:   ", success + fail)
    if problem_folder != []:
        print("\n以下路径文件由于某些原因未能转换：")
        for i in problem_folder:
            print("-"*50)
            # print(i[0] + "\t" + i[1].encode("GB18030"))
            try:
                print(i[0] + "\n" + i[1])
            except UnicodeEncodeError:
                print(i[0] + "\t" + i[1].encode("gbk", "ignore").decode("gbk"))
        print("-"*50)
        #if "y" in input("是否打开这些文件夹(yes/no): ".encode("gbk")).lower():
        if "y" in input("是否打开这些文件夹(yes/no): ").lower():
            for i in problem_folder:
                os.system("explorer " + i[0])

    print("\nDeveloped by Call_Now_Yeah")
    input("Press \"Enter\" to exit")




# main()
if __name__ == "__main__":
    if not os.path.exists(bili_path):
        print("找不到路径", bili_path)
        input("按回车键退出")
        sys.exit()
    main()
