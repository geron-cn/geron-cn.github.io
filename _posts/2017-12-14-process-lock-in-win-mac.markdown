---
layout:  post
title:   Win Unix跨平台平台的进程锁
date:    2017-12-06 10:19:56
author: Gero
header-img: "img/post-bg-miui6.jpg"
tags:
    - 进程锁
    - ProcessLock
---

进程锁，采用常见的文件锁，当时在OSX平台下也鼓捣了不短时间，所以记录下：

入口类， creator：
{% highlight c# %}
 /// <summary>
    /// lock a file, and handle this file until release lock,\n
    /// it is a writeStrem in win , a fcntl lock in unix.\n
    /// remember to release or dispose when no reference. \n
    /// <b>warnning: in unix, file lock can only check the lock between diffrent process,
    /// use System.Threading.Mutex  instead</b>
    /// </summary>
    public class FileLockHandler : System.IDisposable
    {
        private string lockfilepath = string.Empty;

        protected FileLockHandler()
        {
        }

        public string CurrLockFilePath
        {
            get { return lockfilepath; }
        }

        /// <summary>
        /// create a filelock handle, should be dispose after no reference
        /// </summary>
        public static FileLockHandler Create()
        {
            if (MonoDevelop.Core.Platform.IsWindows)
                return new WinFileLockHandler();
            else
                return new UnixFileLockHandler();
        }


        /// <summary>
        /// lock a filepath as a write handle in unix or win, return false when lock failed\n
        /// @PathTooLongException filepath is too long (maybe>248 on win)\n
        /// @UnauthorizedAccessException access failed\n
        /// @SecurityException  access failed\n
        /// </summary>
        /// <param name="filepath"></param>
        /// <returns></returns>
        public  bool LockFile(string filepath)
        {
            bool islocksuccess = OnLockFile(filepath);
            lockfilepath = filepath;
            return islocksuccess;
        }


        
        protected virtual bool OnLockFile(string filepath)
        {
            return false;
        }


        /// <summary>
        /// check filepath is locked as a write handle in unix or win, return false when lock failed\n
        /// returns true when filepath is locked or <b>filepath cannot access</b>
        /// @FileNotFoundException filepath not exists
        /// @PathTooLongException filepath is too long (maybe>248 on win)
        /// @UnauthorizedAccessException access failed
        /// @SecurityException  access failed
        /// </summary>
        /// <param name="filepath"></param>
        /// <returns></returns>
        public bool IsFileLocked(string filePath)
        {
            bool isExists = File.Exists(filePath);
            bool isLocked = isExists;
            if (!isExists)
                return false;
            else
            {
                isLocked = OnIsFileLocked(filePath);
            }
            return isLocked;
        }

        protected virtual bool OnIsFileLocked(string filePath)
        {
            return false;
        }

        public void ReleaseLock()
        {
            if (!File.Exists(lockfilepath))
                throw new FileNotFoundException("Locked File in Handler Not Found: ", lockfilepath);
            OnReleaseLock();
            File.Delete(lockfilepath);
            lockfilepath = string.Empty;
        }

        protected virtual void OnReleaseLock()
        {
        }


        /// <summary>
        /// make some long length string path to a short string name
        /// (we can not create file which path is too long maybe>248)
        /// check file name and ensure the return 32 chexadecimal string.
        /// </summary>
        public static string GetMD5String(string filepath)
        {

            filepath = System.IO.Path.Combine(filepath);
            // Create a new instance of the MD5CryptoServiceProvider object.
            var md5Hasher = System.Security.Cryptography.MD5.Create();

            // Convert the input string to a byte array and compute the hash.
            byte[] data = md5Hasher.ComputeHash(Encoding.Default.GetBytes(filepath));

            // Create a new Stringbuilder to collect the bytes
            // and create a string.
            StringBuilder sBuilder = new StringBuilder();

            // Loop through each byte of the hashed data 
            // and format each one as a hexadecimal string.
            for (int i = 0; i < data.Length; i++)
            {
                sBuilder.Append(data[i].ToString("x2"));
            }

            // Return the hexadecimal string.
            return sBuilder.ToString();
        }

       public void Dispose()
        {
           try
           {
               ReleaseLock();
           }
           catch(System.Exception)
           { 
           }
        }

    }
{% endhighlight %}

win 平台，比较容易理解
{% highlight c# %}
class WinFileLockHandler : FileLockHandler
    {
        private FileStream lockwritehandle = null;
        public WinFileLockHandler()
            : base()
        {

        }

        protected override bool OnLockFile(string filePath)
        {
            try
            {
                lockwritehandle = new FileStream(filePath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            }
            catch (System.Exception ex)
            {
                throw new System.Exception("can not lock file: ", ex);
            }
            return true;
        }

        protected override bool OnIsFileLocked(string filePath)
        {
            bool isLocked = false;
            try
            {
                using (var templock = new FileStream(filePath, FileMode.Open, FileAccess.Write, FileShare.None))
                {
                    isLocked = false;
                    templock.Close();
                }
            }
            catch (System.IO.IOException)   
            {
                isLocked = true;
            }
            catch(System.Exception ex)
            {
                throw new System.Exception("can not be a lock file:", ex);
            }
            return isLocked;
        }


        protected override void OnReleaseLock()
        {
            using (lockwritehandle)
            {
                if (lockwritehandle != null)
                {
                    lockwritehandle.Close();
                    lockwritehandle.Dispose();
                }
                else
                    throw new FileNotFoundException("no lock to release");
            }
        }
    }
{% endhighlight %}


Unix 平台，原理为使用 fcntl 操作和读取文件状态， 当软件 dump 的时候，锁文件不会自动销毁，所以如果考虑比较全的话，应该有个清理不在正在使用的锁文件。
{% highlight c# %}
class UnixFileLockHandler : FileLockHandler
    {
        private Flock flockhandle;
        private int flockfd = 0;


        public UnixFileLockHandler()
            : base()
        {
            flockhandle.l_len = 0;
            flockhandle.l_pid = Syscall.getpid();
            flockhandle.l_start = 0;
            flockhandle.l_type = LockType.F_WRLCK;
            flockhandle.l_whence = SeekFlags.SEEK_SET;
        }



        protected override bool OnLockFile(string filepath)
        {
            bool isLocked = false;
            flockhandle.l_type = LockType.F_WRLCK;
            flockfd = Syscall.open(filepath, OpenFlags.O_CREAT | OpenFlags.O_RDWR, FilePermissions.DEFFILEMODE);
            int ret = Syscall.fcntl(flockfd, FcntlCommand.F_SETLK, ref flockhandle);
            if (ret != -1)
                isLocked = true;
            else
                throw new System.InvalidOperationException(filepath + "has already been locked!");
            return isLocked;
        }

        protected override bool OnIsFileLocked(string filePath)
        {
            bool isLocked = true;
            if (filePath == CurrLockFilePath)   //because file lock can not work in the same process(please use mutex instead), 
                return isLocked;

            flockhandle.l_type = LockType.F_WRLCK;
            int tmpfilehd = Syscall.open(filePath, OpenFlags.O_RDWR, FilePermissions.DEFFILEMODE);
            int ret = Syscall.fcntl(tmpfilehd, FcntlCommand.F_SETLK, ref flockhandle);
            if (ret != -1)
                isLocked = false;
            flockhandle.l_type = LockType.F_UNLCK;
            Syscall.fcntl(tmpfilehd, FcntlCommand.F_SETLK, ref flockhandle);
            return isLocked;
        }


        protected override void OnReleaseLock()
        {
            flockhandle.l_type = LockType.F_UNLCK;
            int ret = Syscall.fcntl(flockfd, FcntlCommand.F_SETLK, ref flockhandle);
            if (ret == -1)
            {
                throw new System.InvalidOperationException("Release Lock File failed: " + CurrLockFilePath);
            }
            Syscall.close(flockfd);
        }
    }
{% endhighlight %}